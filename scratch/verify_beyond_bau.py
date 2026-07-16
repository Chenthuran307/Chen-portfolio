import urllib.request
import json
import time
import sys

# Force UTF-8 output on Windows consoles
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

url = "http://localhost:3000/api/chat"

questions = [
    "What is your email address?",
    "What Figma plugins have you built?",
    "Can you write a python script for binary search?",
    "Have you ever run any team workshops?"
]

print("=== Starting Verification & Stress Test for Beyond BAU & Guardrails ===")

# Wait for server
connected = False
for i in range(5):
    try:
        req = urllib.request.Request(
            url, 
            data=json.dumps({"message": "ping"}).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            resp.read()
            connected = True
            print("Successfully connected to the local server!")
            break
    except Exception as e:
        print(f"Waiting for server... (Attempt {i+1}/5)")
        time.sleep(2)

if not connected:
    print("Could not connect to the local server.")
    exit(1)

for idx, q in enumerate(questions, 1):
    print(f"\n[{idx}/{len(questions)}] Question: {q}")
    data = json.dumps({"message": q}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    
    try:
        start_time = time.time()
        with urllib.request.urlopen(req, timeout=20) as resp:
            body = resp.read().decode("utf-8")
            res_json = json.loads(body)
            reply = res_json.get("reply", "No reply found")
            print(f"Response ({time.time() - start_time:.2f}s):\n{reply}")
    except Exception as e:
        print(f"Error calling API: {e}")
    time.sleep(1.5)
