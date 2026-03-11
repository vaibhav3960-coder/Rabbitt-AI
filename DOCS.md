# FireReach - Autonomous Outreach Engine

FireReach is a high-performance autonomous outreach prototype for SDRs/GTM teams. Powered by **Groq (LLaMA 3.3-70B)**, the engine captures live buyer signals, analyzes them against an Ideal Customer Profile (ICP), and generates zero-template, hyper-personalized outreach emails.

## Setup Instructions

### Pre-requisites
- [Groq API Key](https://console.groq.com/keys)

### 1. Backend Setup
1. Navigate to the `backend/` directory.
2. Create/Update a `.env` file and add your Groq API Key:
   ```env
   GROQ_API_KEY=your_groq_api_key_here
   ```
3. Install dependencies: `pip install -r requirements.txt`
4. Run the backend server: `uvicorn main:app --reload`

### 2. Frontend Setup
1. Navigate to the `frontend/` directory.
2. Install dependencies: `npm install`
3. Run the development server: `npm run dev`
4. Open the provided Vite URL (typically `http://localhost:5173`).

---

## Logic Flow
The engine follows a strict Sequential Reasoning flow:
1. **Signal Capture:** The `tool_signal_harvester` retrieves live intent triggers (funding, hiring, tech stack).
2. **Contextual Research:** The `tool_research_analyst` correlates these signals with the user's ICP to generate an Account Brief.
3. **Automated Delivery:** The `tool_outreach_automated_sender` applies a Zero-Template Policy to draft a personalized email based on the brief.
4. **Final Orchestration:** The LLaMA 3.3 orchestrator ensures the exact company names and signal data are mapped dynamically into the final output.

## System Instruction
The agent is governed by a strict Zero-Template and Dynamic Mapping policy to ensure no generic placeholders (like `[Amount]` or `[Company]`) are ever returned to the user.

---

## Features
- **Live Execution Console:** Real-time visibility into the agent's step-by-step reasoning.
- **Signals Visualization:** Dedicated UI component displaying exactly which buyer signals were harvested.
- **Automated Delivery Banners:** Instant confirmation of successful outreach.
- **Premium Design:** Immersive space-themed dark mode using TailwindCSS and React.
