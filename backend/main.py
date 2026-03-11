import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from agent import run_fire_reach_agent
import uvicorn

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

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
