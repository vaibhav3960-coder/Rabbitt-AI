FireReach - Autonomous Outreach Engine: Walkthrough
1. Overview
The FireReach prototype has been fully implemented and is now live!

Live URL: https://rabbitt-ai-mu.vercel.app

It features a modern, visually stunning React dashboard (Vite + TailwindCSS) and a high-performance FastAPI backend powered by Groq (LLaMA 3.3-70B) operating in an autonomous function-calling loop.

2. Objective Completion
The Agentic Toolset: Implemented exactly three tools:
tool_signal_harvester
: Captures Live Buyer Signals (funding rounds, hiring trends).
tool_research_analyst
: Analyzes signals against the ICP to generate an Account Brief.
tool_outreach_automated_sender
: Transforms research into a hyper-personalized email (Zero-Template).
Sequential Reasoning: The orchestrator enforces the flow: Signals -> Analysis -> Outreach.
Bypassing Limits: Migrated from Gemini to Groq to ensure reliable, high-speed execution without being blocked by free-tier daily quotas.
3. Execution Flow
User Input: The SDR inputs their ICP and Task Objective on the dashboard.
Orchestration: The request hits the FastAPI endpoint /api/run-agent.
Loop: The LLaMA 3.3 orchestrator receives the prompt.
Tool: Harvester: The agent calls 
tool_signal_harvester
 and retrieves CyberShield Inc.'s $20M Series B.
Tool: Analyst: The agent passes the real data to 
tool_research_analyst
 to map expansion to security needs.
Tool: Sender: The agent drafts a zero-template email using the exact signals (e.g., "$20M Series B") and calls the sender tool.
Return: The backend returns the step-by-step history and the final drafted email to the frontend.
4. Verification Details
Detailed Visibility: The "Live Execution Console" and "Final Output" now clearly display the research brief and the full text of the drafted email, ensuring complete transparency into the agent's work.
Strict Dynamic Mapping: Verified that the agent extracts exact data (e.g., "$20M Series B" and "CyberShield Inc.") from tools and injects them into the email, satisfying the Zero-Template Policy perfectly. No generic placeholders like [Company Name] remain.
Robust Orchestration: Transitioned to Groq LLaMA 3.3 to provide high-speed, reliable performance with advanced tool-calling support.
5. Visual Aesthetics
The dashboard features an immersive space-themed dark mode with glowing indigo accents and glassmorphism components. It is optimized for a premium user experience that feels proactive and high-tech.

Agent
Rabbitt AI Project



AI may make mistakes. Double-check all generated code.
