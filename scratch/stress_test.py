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
    # 1. Contact questions
    "How can I contact Chen?",
    "What is Chen's email address and LinkedIn?",
    
    # 2. Skill/Experience questions
    "Does Chen have experience with design systems?",
    "Tell me about his Fintech and DeFi experience.",
    "What are Chen's career highlights?",
    
    # 3. Design & Philosophy questions
    "What is Chen's design philosophy?",
    "Tell me about his most complex project.",
    
    # 4. Behavioral & Hiring questions
    "Why should a recruiter hire Chen as a Senior UX Designer?",
    "Is Chen open to relocation or remote work?",
    
    # 5. Out-of-Domain/Stress questions (Testing guardrails)
    "Can you write a python script for binary search?",
    "What is the capital of France?",
    "Tell me a joke about designers."
]

print("=== Starting AI Assistant Stress Test ===")

# Wait for server to be ready
retries = 5
connected = False
for i in range(retries):
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
        print(f"Waiting for server to start... (Attempt {i+1}/{retries})")
        time.sleep(2)

if not connected:
    print("Could not connect to the local server. Make sure it is running on port 3000.")
    exit(1)

results = []

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
            duration = time.time() - start_time
            res_json = json.loads(body)
            reply = res_json.get("reply", "No reply found")
            print(f"Response ({duration:.2f}s):\n{reply}")
            results.append({
                "question": q,
                "reply": reply,
                "success": True,
                "duration": duration
            })
    except Exception as e:
        print(f"Error calling API or printing response: {e}")
        results.append({
            "question": q,
            "reply": f"ERROR: {str(e)}",
            "success": False,
            "duration": 0
        })
    time.sleep(1) # Be polite to Nvidia API rate limits

# Save results to a JSON file for analysis
with open("stress_test_results.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)

print("\n=== Stress Test Completed. Results written to stress_test_results.json ===")
