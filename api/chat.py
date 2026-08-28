from http.server import BaseHTTPRequestHandler
import json
import urllib.request
import urllib.error
import os

# Never hard-code the key. Set NVIDIA_API_KEY in the environment
# (Vercel project settings, or a local .env file which is gitignored).
NVIDIA_API_KEY = os.environ.get("NVIDIA_API_KEY")
NVIDIA_API_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
# meta/llama-3.1-8b-instruct reached end-of-life 2026-08-26 and now returns HTTP 410.
MODEL = os.environ.get("NVIDIA_MODEL", "openai/gpt-oss-20b")

from api.prompt_loader import get_system_prompt

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)

        try:
            data = json.loads(body)
            user_message = data.get("message", "").strip()
            if not user_message:
                raise ValueError("Empty message")

            payload = json.dumps({
                "model": MODEL,
                "messages": [
                    {"role": "system", "content": get_system_prompt()},
                    {"role": "user", "content": user_message}
                ],
                "temperature": 0.5,
                "max_tokens": 300,
                "stream": False
            }).encode("utf-8")

            req = urllib.request.Request(
                NVIDIA_API_URL,
                data=payload,
                headers={
                    "Authorization": f"Bearer {NVIDIA_API_KEY}",
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                },
                method="POST"
            )

            # Diagnostics are only attached when the caller explicitly asks for
            # them (?debug=1). Visitors never see them, and the key is never
            # echoed back — only whether one is present and how long it is.
            want_debug = "debug=1" in (self.path or "")
            debug = {
                "model": MODEL,
                "key_present": bool(NVIDIA_API_KEY),
                "key_len": len(NVIDIA_API_KEY or ""),
                "key_prefix": (NVIDIA_API_KEY or "")[:6],
            }

            # Direct sync request for serverless function
            try:
                with urllib.request.urlopen(req, timeout=25) as resp:
                    result = json.loads(resp.read().decode("utf-8"))
                reply = result["choices"][0]["message"]["content"].strip()
                debug["upstream"] = 200
            except urllib.error.HTTPError as e:
                error_body = e.read().decode("utf-8")
                print(f"API Error {e.code}: {error_body}")
                debug["upstream"] = e.code
                debug["upstream_body"] = error_body[:300]
                reply = "I'm having trouble reaching the AI right now. Please try again in a moment, or visit the Contact page directly."
            except Exception as e:
                print(f"Connection Error: {e}")
                debug["upstream"] = "connection_error"
                debug["upstream_body"] = str(e)[:300]
                reply = "Sorry, I timed out. Please try again shortly."

            out = {"reply": reply}
            if want_debug:
                out["debug"] = debug
            self._send_json(200, out)

        except Exception as e:
            print(f"Server error: {e}")
            self._send_json(500, {"reply": "Something went wrong. Please try again."})

    def _send_json(self, code, data):
        body = json.dumps(data).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)
