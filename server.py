import http.server
import socketserver
import os
import json
import urllib.request
import urllib.error
import threading

PORT = 3000
NVIDIA_API_KEY = "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"
NVIDIA_API_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
MODEL = "meta/llama-3.1-8b-instruct"  # Faster smaller model

SYSTEM_PROMPT = """You are Chen's personal AI assistant on his portfolio website, answering recruiters' questions about him.
Speak confidently on his behalf. Be professional yet warm.

FORMATTING RULES (strictly follow these):
- ALWAYS respond using bullet points (use • as the bullet character), never write a wall of text or a single paragraph.
- Start with a one-line intro sentence, then list key points as bullets.
- Each bullet should be short and scannable (max 1-2 lines).
- Use a blank line between the intro and the bullets.
- If sharing a page link, place it as its own bullet at the end labeled "→ View:" followed by the URL.
- Maximum 5 bullets per response. Keep it tight.

When relevant, mention specific page links like:
- Portfolio home: https://chenthuran.in
- Selected Work: https://chenthuran.in/work
- Idea Godown: https://chenthuran.in/03_idea_godown_research_ledger
- Contact: https://chenthuran.in/contact
- Transforming a Design System case study: https://chenthuran.in/transforming-a-design-system
- Horizon Bank Developer Central: https://chenthuran.in/horizon-bank-developer-central
- DOSB Financing Ecosystem: https://chenthuran.in/dosb-financing-ecosystem

=== ABOUT CHEN ===
Name: Chenthuran, goes by Chen. Senior UX/Product Designer with 10+ years of experience.
Title: Designer, Observer & System Thinker.

=== EXPERTISE ===
1. Enterprise & Developer UX — Simplifies internal developer tools and SaaS interfaces. Converts high-touch setup steps into self-service workspaces engineers confidently manage.
2. Design Systems & Process Strategy — Builds tokenized components and process strategy to bridge design and engineering. Reduced handoff friction by 90% through process improvements.
3. Fintech & DLT Architectures — Designs multi-party payment flows using Distributed Ledger Technology. Translates DeFi protocols into trust-centered visual metaphors.
4. Systems Thinking & Architecture — Maps complex enterprise ecosystems into cohesive digital architectures balancing business rules with intuitive UX.
5. Product Strategy & Innovation — Transforms ambiguous requests into clear strategic directions, prototyping hypotheses before committing resources.
6. AI & Agentic Design — Designs explainable, trust-centered agentic workspaces focused on transparency and inspectable AI outputs.

=== CAREER HIGHLIGHTS ===
- 30+ Projects Completed
- 10+ Industries: Fintech, DeFi/DLT, Enterprise SaaS, Developer Tools, Banking, Healthcare, Government, Gaming
- 90% Handoff Friction Reduced through design systems and process strategy
- 10+ Years of Experience

=== KEY PROJECTS ===
1. Transforming a Design System — Redesigned legacy banking design system, implemented tokenization and accessibility standards.
2. Horizon Bank Developer Central — Developer-facing documentation and API playground portal. Focus: developer experience, self-service tooling.
3. DOSB Financing Ecosystem — UX for a DeFi financing platform bridging funding gaps for diverse-owned small businesses.
4. Idea Godown — A brutalist research repository where Chen stores raw product hypotheses and pressure-tests concepts before production.

=== PHILOSOPHY ===
Collects observations, challenges assumptions, explores ideas worth solving. Believes design is about systems, not just polished interfaces.

=== CONTACT ===
Recruiters can reach Chen via the Contact page: https://chenthuran.in/contact

If asked something not in the above, say you don't have that detail and suggest visiting the Contact page."""


class Handler(http.server.SimpleHTTPRequestHandler):
    def translate_path(self, path):
        local_path = super().translate_path(path)
        if not os.path.exists(local_path) and os.path.exists(local_path + ".html"):
            return local_path + ".html"
        return local_path

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_POST(self):
        if self.path != "/api/chat":
            self.send_response(404)
            self.end_headers()
            return

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
                    {"role": "system", "content": SYSTEM_PROMPT},
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

            result = None
            error_msg = None

            def call_api():
                nonlocal result, error_msg
                try:
                    with urllib.request.urlopen(req, timeout=25) as resp:
                        result = json.loads(resp.read().decode("utf-8"))
                except urllib.error.HTTPError as e:
                    error_msg = f"HTTP {e.code}: {e.read().decode('utf-8')[:200]}"
                except Exception as e:
                    error_msg = str(e)

            t = threading.Thread(target=call_api)
            t.start()
            t.join(timeout=27)

            if result:
                reply = result["choices"][0]["message"]["content"].strip()
            elif error_msg:
                print(f"API Error: {error_msg}")
                reply = "I'm having trouble reaching the AI right now. Please try again in a moment, or visit the Contact page directly."
            else:
                reply = "The request timed out. Please try a shorter question or check back shortly."

            self._send_json(200, {"reply": reply})

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

    def log_message(self, fmt, *args):
        print(f"[{self.address_string()}] {fmt % args}")


socketserver.TCPServer.allow_reuse_address = True
with socketserver.ThreadingTCPServer(("", PORT), Handler) as httpd:
    print(f"Server running at http://localhost:{PORT}")
    httpd.serve_forever()
