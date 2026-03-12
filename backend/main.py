import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from agent import run_fire_reach_agent, _update_stats, _update_memory
import uvicorn
import json

load_dotenv()

app = FastAPI(title="FireReach Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow frontend to access
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AgentRequest(BaseModel):
    icp: str
    task: str
    target_email: str

class EmailApprove(BaseModel):
    email_copy: str
    target_email: str
    target_company: str = "Unknown"

@app.post("/api/run-agent")
def run_agent(req: AgentRequest):
    try:
        if not os.getenv("GROQ_API_KEY"):
            return {
                "final_result": "Error: GROQ_API_KEY environment variable is not set. Please set it in the backend.",
                "history": []
            }
            
        result = run_fire_reach_agent(req.icp, req.task, req.target_email)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/approve-send")
async def approve_send(request: EmailApprove):
    # In a real app, this would integrate with SendGrid/AWS SES
    # Here we simulate the final dispatch
    print(f"DEBUG: FINAL DISPATCH to {request.target_email}")
    print(f"DEBUG: CONTENT:\n{request.email_copy}")
    
    # Phase 6: Sync stats
    _update_stats("emails_sent", 1)
    
    # Phase 7: Persist memory
    if request.target_company and request.target_company != "Unknown":
        _update_memory(request.target_company, "contacted")
    
    return {"status": "success", "message": f"Email officially sent to {request.target_email}"}

@app.get("/api/stats")
async def get_stats():
    stats_file = os.path.join(os.path.dirname(__file__), "stats.json")
    if not os.path.exists(stats_file):
        return {"signals_detected": 0, "emails_generated": 0, "emails_sent": 0}
    with open(stats_file, "r") as f:
        return json.load(f)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
