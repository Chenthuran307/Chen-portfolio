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
from api.local_responder import generate_local_response

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        self._send_json(200, {
            "status": "online",
            "service": "Portfolio AI Assistant API",
            "instruction": "Send a POST request with JSON body: {\"message\": \"your question\"} to chat with Chen's AI assistant."
        })

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)

        try:
            data = json.loads(body)
            user_message = data.get("message", "").strip()
            if not user_message:
                raise ValueError("Empty message")

            reply = None

            if NVIDIA_API_KEY:
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

                try:
                    # Timeout at 6s to stay well below Vercel's 10s maximum execution limit
                    with urllib.request.urlopen(req, timeout=6) as resp:
                        result = json.loads(resp.read().decode("utf-8"))
                    if result and "choices" in result and len(result["choices"]) > 0:
                        reply = result["choices"][0]["message"]["content"].strip()
                except urllib.error.HTTPError as e:
                    error_body = e.read().decode("utf-8")
                    print(f"API Error {e.code}: {error_body}. Activating local fallback.")
                except Exception as e:
                    print(f"Connection / Timeout Error: {e}. Activating local fallback.")

            # Fallback to intelligent local responder if upstream is unavailable, unauthorized, or timed out
            if not reply:
                reply = generate_local_response(user_message)

            self._send_json(200, {"reply": reply})

        except Exception as e:
            print(f"Server error: {e}")
            try:
                local_reply = generate_local_response(user_message if 'user_message' in locals() and user_message else "")
                self._send_json(200, {"reply": local_reply})
            except Exception:
                self._send_json(500, {"reply": "Something went wrong. Please try again."})

    def _send_json(self, code, data):
        body = json.dumps(data).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)
