import http.server
import socketserver
import os
import json
import urllib.request
import urllib.error
import threading
import subprocess
import re

PORT = 3000
NVIDIA_API_KEY = "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"
NVIDIA_API_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
MODEL = "meta/llama-3.1-8b-instruct"  # Faster smaller model

from api.prompt_loader import get_system_prompt

# Deployment global state
deploy_running = False
deploy_log_path = "deploy.log"

def extract_element_by_id(html_content, element_id):
    pattern = rf'<([a-zA-Z0-9]+)[^>]*id="{element_id}"[^>]*>(.*?)</\1>'
    match = re.search(pattern, html_content, flags=re.DOTALL)
    if match:
        return match.group(2).strip()
    return ""

def update_element_by_id(html_content, element_id, new_text):
    pattern = rf'(<([a-zA-Z0-9]+)[^>]*id="{element_id}"[^>]*>)(.*?)(</\2>)'
    
    def repl(m):
        tag_name = m.group(2).lower()
        if tag_name in ['span', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            # Keep inline to prevent breaking CSS layouts with whitespace wrapping
            return m.group(1) + new_text + m.group(4)
        else:
            # Multi-line/block tags get standard indentation
            return m.group(1) + "\n          " + new_text + "\n        " + m.group(4)
            
    return re.sub(pattern, repl, html_content, flags=re.DOTALL)

def run_deployment():
    global deploy_running
    deploy_running = True
    
    with open(deploy_log_path, "w", encoding="utf-8") as log_file:
        log_file.write("=== Starting One-Click Portfolio Deployment ===\n")
        log_file.write(f"Working Directory: {os.getcwd()}\n\n")
        log_file.flush()
        
        # Windows-safe commands as single strings (protects double quotes)
        commands = [
            "git status",
            "git add .",
            'git commit -m "Update portfolio content via dashboard"',
            "git push origin main",
            "npx vercel --prod --yes"
        ]
        
        for cmd in commands:
            log_file.write(f"\n> Running: {cmd}\n")
            log_file.flush()
            try:
                process = subprocess.Popen(
                    cmd, 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.STDOUT, 
                    text=True, 
                    shell=True
                )
                
                # Read output in real-time
                for line in process.stdout:
                    log_file.write(line)
                    log_file.flush()
                
                process.wait()
                if process.returncode != 0:
                    # Ignore git commit error if working tree is clean
                    if "git commit" in cmd and process.returncode == 1:
                        log_file.write("No local changes to commit. Proceeding...\n")
                        log_file.flush()
                        continue
                    log_file.write(f"\n[Error] Command failed with exit code: {process.returncode}\n")
                    log_file.flush()
                    break
            except Exception as e:
                log_file.write(f"[Error] Command execution error: {e}\n")
                log_file.flush()
                break
        else:
            log_file.write("\n=== Deployment Completed Successfully! 🎉 ===\n")
            log_file.flush()
            
    deploy_running = False


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

    def do_GET(self):
        # /dashboard mapping
        if self.path == "/dashboard" or self.path == "/dashboard.html":
            self.path = "/stitch/html/dashboard.html"
            super().do_GET()
            return

        if self.path == "/api/dashboard/load":
            self._handle_load()
        elif self.path == "/api/dashboard/deploy-log":
            self._handle_deploy_log()
        else:
            super().do_GET()

    def do_POST(self):
        if self.path == "/api/chat":
            self._handle_chat()
        elif self.path == "/api/dashboard/save":
            self._handle_save()
        elif self.path == "/api/dashboard/deploy":
            self._handle_deploy()
        else:
            self.send_response(404)
            self.end_headers()

    def _handle_chat(self):
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

    def _handle_load(self):
        # 1. Read Hero Content and Projects from index.html (or fallback to 01_home.html)
        html_path = os.path.join("stitch", "html", "index.html")
        if not os.path.exists(html_path):
            html_path = os.path.join("stitch", "html", "01_home.html")
            
        hero_title = ""
        hero_subtitle = ""
        hero_about = ""
        
        projects = {}
        
        if os.path.exists(html_path):
            try:
                with open(html_path, "r", encoding="utf-8") as f:
                    html_content = f.read()
                hero_title = extract_element_by_id(html_content, "hero-title")
                hero_subtitle = extract_element_by_id(html_content, "hero-subtitle")
                hero_about = extract_element_by_id(html_content, "hero-about")
                
                # Load Projects 1-3
                for i in range(1, 4):
                    projects[f"project{i}_tag"] = extract_element_by_id(html_content, f"project{i}-tag")
                    projects[f"project{i}_title"] = extract_element_by_id(html_content, f"project{i}-title")
                    projects[f"project{i}_desc"] = extract_element_by_id(html_content, f"project{i}-desc")
            except Exception as e:
                print(f"Error reading HTML: {e}")

        # 2. Read Idea Godown items from 03_idea_godown_research_ledger.html
        ledger_path = os.path.join("stitch", "html", "03_idea_godown_research_ledger.html")
        ideas = {}
        if os.path.exists(ledger_path):
            try:
                with open(ledger_path, "r", encoding="utf-8") as f:
                    ledger_content = f.read()
                for i in range(1, 8):
                    ideas[f"idea{i}_title"] = extract_element_by_id(ledger_content, f"idea{i}-title")
                    ideas[f"idea{i}_idea"] = extract_element_by_id(ledger_content, f"idea{i}-idea")
            except Exception as e:
                print(f"Error reading ledger HTML: {e}")

        # 3. Read Prompt JSON configuration
        json_path = os.path.join("api", "prompt.json")
        json_data = {}
        if os.path.exists(json_path):
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    json_data = json.load(f)
            except Exception as e:
                print(f"Error reading prompt.json: {e}")

        response_data = {
            "hero_title": hero_title,
            "hero_subtitle": hero_subtitle,
            "hero_about": hero_about,
            "name": json_data.get("name", "Chenthuran"),
            "title": json_data.get("title", ""),
            "about": json_data.get("about", ""),
            "expertise": json_data.get("expertise", []),
            "highlights": json_data.get("highlights", []),
            "projects": projects,
            "ideas": ideas
        }
        self._send_json(200, response_data)

    def _handle_save(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        
        try:
            data = json.loads(body)
            
            # 1. Save Hero Content and Projects to index.html and 01_home.html
            hero_title = data.get("hero_title", "").strip()
            hero_subtitle = data.get("hero_subtitle", "").strip()
            hero_about = data.get("hero_about", "").strip()
            projects = data.get("projects", {})
            
            pages = ["index.html", "01_home.html"]
            for page in pages:
                path = os.path.join("stitch", "html", page)
                if os.path.exists(path):
                    with open(path, "r", encoding="utf-8") as f:
                        content = f.read()
                    
                    content = update_element_by_id(content, "hero-title", hero_title)
                    content = update_element_by_id(content, "hero-subtitle", hero_subtitle)
                    content = update_element_by_id(content, "hero-about", hero_about)
                    
                    # Update Projects 1-3
                    for i in range(1, 4):
                        p_tag = projects.get(f"project{i}_tag", "").strip()
                        p_title = projects.get(f"project{i}_title", "").strip()
                        p_desc = projects.get(f"project{i}_desc", "").strip()
                        
                        if p_tag: content = update_element_by_id(content, f"project{i}-tag", p_tag)
                        if p_title: content = update_element_by_id(content, f"project{i}-title", p_title)
                        if p_desc: content = update_element_by_id(content, f"project{i}-desc", p_desc)
                    
                    with open(path, "w", encoding="utf-8") as f:
                        f.write(content)
            
            # 2. Save Projects to work.html
            work_path = os.path.join("stitch", "html", "work.html")
            if os.path.exists(work_path):
                with open(work_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # Update Projects 1-3
                for i in range(1, 4):
                    p_tag = projects.get(f"project{i}_tag", "").strip()
                    p_title = projects.get(f"project{i}_title", "").strip()
                    p_desc = projects.get(f"project{i}_desc", "").strip()
                    
                    if p_tag: content = update_element_by_id(content, f"project{i}-tag", p_tag)
                    if p_title: content = update_element_by_id(content, f"project{i}-title", p_title)
                    if p_desc: content = update_element_by_id(content, f"project{i}-desc", p_desc)
                
                with open(work_path, "w", encoding="utf-8") as f:
                    f.write(content)
                    
            # 3. Save Idea Godown items to 03_idea_godown_research_ledger.html
            ideas = data.get("ideas", {})
            ledger_path = os.path.join("stitch", "html", "03_idea_godown_research_ledger.html")
            if os.path.exists(ledger_path):
                with open(ledger_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                for i in range(1, 8):
                    idea_title = ideas.get(f"idea{i}_title", "").strip()
                    idea_desc = ideas.get(f"idea{i}_idea", "").strip()
                    
                    if idea_title: content = update_element_by_id(content, f"idea{i}-title", idea_title)
                    if idea_desc: content = update_element_by_id(content, f"idea{i}-idea", idea_desc)
                    
                with open(ledger_path, "w", encoding="utf-8") as f:
                    f.write(content)
                        
            # 4. Save Dynamic Prompt Settings
            json_path = os.path.join("api", "prompt.json")
            json_data = {
                "name": data.get("name", "Chenthuran").strip(),
                "title": data.get("title", "").strip(),
                "about": data.get("about", "").strip(),
                "expertise": [item.strip() for item in data.get("expertise", []) if item.strip()],
                "highlights": [item.strip() for item in data.get("highlights", []) if item.strip()]
            }
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(json_data, f, indent=2)
                
            self._send_json(200, {"status": "success"})
        except Exception as e:
            print(f"Error saving: {e}")
            self._send_json(500, {"status": "error", "message": str(e)})

    def _handle_deploy(self):
        global deploy_running
        if deploy_running:
            self._send_json(400, {"status": "error", "message": "Deployment is already running."})
            return
            
        t = threading.Thread(target=run_deployment)
        t.start()
        self._send_json(200, {"status": "success", "message": "Deployment started."})

    def _handle_deploy_log(self):
        if not os.path.exists(deploy_log_path):
            self._send_json(200, {"log": "No deployment log found. Click deploy to start.", "running": False})
            return
            
        try:
            with open(deploy_log_path, "r", encoding="utf-8") as f:
                log_content = f.read()
        except Exception as e:
            log_content = f"Error reading log file: {e}"
            
        self._send_json(200, {"log": log_content, "running": deploy_running})

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
