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
        response = requests.post(url, json=payload, headers=headers, timeout=60)
        if response.status_code == 200:
            data = response.json()
            print("\n--- FINAL RESULT ---")
            print(data.get("final_result", "No final result found"))
            print("\n--- AGENT HISTORY ---")
            for step in data.get("history", []):
                print(f"[{step['role'].upper()}]\n{step['content']}\n")
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
