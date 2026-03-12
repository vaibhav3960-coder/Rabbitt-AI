import requests
import json
import time

url = "http://localhost:8000/api/run-agent"
payload = {
    "icp": "We sell high-end cybersecurity training to Series B startups.",
    "task": "Find companies with recent growth signals and send a personalized outreach email to candidate@example.com that connects their expansion to our security training.",
    "target_email": "candidate@example.com"
}
headers = {"Content-Type": "application/json"}

print("Triggering Agent...")

max_retries = 3
for attempt in range(max_retries):
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=180)
        if response.status_code == 200:
            data = response.json()
            print("\n--- FINAL AGENT RESULT ---")
            print(data.get("final_result", "No final result found"))
            
            # Phase 5 Check: Handle Draft Ready
            draft_step = next((s for s in data.get("history", []) if s.get("type") == "observation" and "draft_ready" in s.get("content", "")), None)
            
            if draft_step:
                print("\n[PHASE 5] Draft ready for approval. Simulating user 'Approve & Send'...")
                import json
                draft_content = json.loads(draft_step['content'])
                
                # Hit the new approval endpoint
                approve_res = requests.post(
                    "http://localhost:8000/api/approve-send",
                    json={
                        "email_copy": draft_content["email_copy"],
                        "target_email": draft_content["sent_to"]
                    }
                )
                print(f"[PHASE 5] Approval Response: {approve_res.json()}")
            
            print("\n--- AGENT HISTORY ---")
            for step in data.get("history", []):
                role = step.get('role', 'UNKNOWN').upper()
                step_type = step.get('type', 'content').upper()
                content = step.get('content', '')
                
                if step_type == "THOUGHT":
                    print(f"[{role} THOUGHT] 💭\n{content}\n")
                elif step_type == "ACTION":
                    print(f"[{role} ACTION] 🛠️\nCalling {step.get('tool')} with {step.get('args')}\n")
                elif step_type == "OBSERVATION":
                    print(f"[{role} OBSERVATION] 👁️\n{content}\n")
                elif step_type == "DECISION":
                    print(f"[{role} DECISION] ✅\n{content}\n")
                else:
                    print(f"[{role}]\n{content}\n")
            break
        elif response.status_code == 500 and "429" in response.text:
            print(f"Rate limit hit. Waiting 70 seconds before retry {attempt + 1}/{max_retries}...")
            time.sleep(70)
        else:
            print(f"Error {response.status_code}: {response.text}")
            break
    except Exception as e:
        print(f"Exception occurred: {e}")
        break
