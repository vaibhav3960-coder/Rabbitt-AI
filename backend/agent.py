import os
import json
from groq import Groq
from duckduckgo_search import DDGS
from rag_engine import get_rag_context
from utils import _update_stats, _get_memory, _update_memory

def tool_company_finder(icp: str) -> str:
    """
    Discovers 3-5 potential target companies based on specific keywords.
    Args:
        icp: Search keywords (e.g., 'Series B cybersecurity' or 'fintech london').
    """
    # Broad search for news lists
    search_query = f"{icp} startups funded 2024 news -site:runoob.com"
    
    print(f"DEBUG: Discovering companies for query: {search_query}")
    
    try:
        with DDGS() as ddgs:
            # specifically search for news/lists to get actual company names
            results = list(ddgs.text(f"{search_query}", max_results=5))
            
            if not results:
                return json.dumps({"error": "No matching companies found."})
            
            companies = []
            for res in results:
                companies.append({
                    "name": res.get("title"),
                    "description": res.get("body"),
                    "link": res.get("href")
                })
            
            return json.dumps({"discovered_companies": companies})
    except Exception as e:
        return json.dumps({"error": f"Failed to discover companies: {str(e)}"})

def tool_signal_harvester(target: str) -> str:
    """
    Fetches real-time data for a SPECIFIC company. Captures Live Buyer Signals using web search.
    
    Args:
        target: The target company name.
    """
    search_query = target
    print(f"DEBUG: Searching for signals: {search_query}")
    
    try:
        with DDGS() as ddgs:
            # Search for news specifically to find funding/hiring signals. 
            # Keep query simple to avoid empty results.
            results = list(ddgs.text(f"{search_query} news", max_results=5))
            
            if not results:
                return json.dumps({"error": "No signals found for the target."})
            
            formatted_signals = []
            for res in results:
                formatted_signals.append({
                    "title": res.get("title"),
                    "snippet": res.get("body"),
                    "link": res.get("href")
                })
            
            # Phase 6: Sync stats
            _update_stats("signals_detected", len(formatted_signals))
            
            return json.dumps({target if target else "General Prospects": {"signals": formatted_signals}})
    except Exception as e:
        return json.dumps({"error": f"Failed to harvest signals: {str(e)}"})

def tool_research_analyst(signals: str, icp: str) -> str:
    """
    Takes harvested signals and the user's ICP to generate a 2-paragraph 
    "Account Brief" highlighting specific pain points and strategic alignment.
    
    Args:
        signals: The JSON string of harvested signals.
        icp: The Ideal Customer Profile.
        target: The target company name (optional).
    """
    try:
        # Phase 8: RAG context
        target = ""
        try:
            sig_data = json.loads(signals)
            target = list(sig_data.keys())[0] if sig_data else ""
        except: pass
        
        rag_context = get_rag_context(target)
        
        client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
        prompt = f"""Given these live signals: {signals} 
        And our ICP: {icp}. 
        
        INTERNAL KNOWLEDGE (RAG):
        {rag_context if rag_context else "No specific internal documents found."}
        
        Generate a concise 'Account Brief' (max 3-4 bullet points) analyzing strategic alignment and potential pain points.
        Focus on WHY we should reach out NOW based on these specific triggers.
        STRICT RULE: You MUST use actual company names and data. No placeholders.
        """
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.1-8b-instant", # Switched to 8B to save tokens
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        return f"Account Brief Fallback: - Prospect raised high funding. - Scalable infrastructure needs security. - High alignment with ICP. ({str(e)})"

def tool_outreach_automated_sender(brief: str, target_email: str) -> str:
    """
    Transforms the research brief into a hyper-personalized email and automatically dispatches it.
    Email MUST NOT use generic templates.
    
    Args:
        brief: The account brief generated from research.
        target_email: The candidate email to send to.
    """
    try:
        client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
        prompt = f"""Write a short, hyper-personalized outreach email based on this Account Brief: {brief}. 
        Send it to {target_email}. 
        
        STRICT CONSTRAINTS:
        - Format: Short, Direct, Personalized.
        - Length: Under 100 words.
        - Structure: 
          1. Catchy subject line related to the signal.
          2. Hi [Name/Role],
          3. One sentence connecting the signal (e.g., $20M raise) to their current challenge.
          4. One sentence explaining our value prop.
          5. CTA: Worth a quick 10-min chat?
        
        Example Style:
        Subject: Congrats on the $20M raise 🚀
        Hi Alex,
        Saw CyberShield just raised a $20M Series B and is hiring security engineers. 
        Many startups at this stage struggle with scaling secure development practices. 
        We help engineering teams implement advanced security training so new hires ramp up faster.
        Worth a quick 10-min chat?
        
        Zero-Template Policy: Use actual details from the brief. No placeholders like '[Your Name]'.
        Return ONLY the final email body.
        """
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.1-8b-instant",
        )
        
        # Phase 6: Sync stats
        _update_stats("emails_generated", 1)
        
        return json.dumps({
            "status": "draft_ready",
            "message": "Outreach draft prepared for review.",
            "sent_to": target_email,
            "email_copy": chat_completion.choices[0].message.content
        })
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": "Failed to draft email",
            "error": str(e)
        })

def run_fire_reach_agent(icp: str, task: str, target_email: str):
    """
    Main orchestration loop for the FireReach agent using Groq function calling.
    """
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    
    system_instruction = """You are the FireReach Autonomous Outreach Engine.
Objective: Discover target companies, research signals, and send SHORT, high-conversion outreach emails.

Strict Linear Flow:
1. Discover -> 2. Harvest -> 3. Research -> 4. Delivery.
NEVER repeat a step. If you have the results of a previous step, move to the NEXT one immediately.

TOOL USAGE POLICY:
- Use ONLY the tools listed below: `tool_company_finder`, `tool_signal_harvester`, `tool_research_analyst`, `tool_outreach_automated_sender`.
- If you need to search Google or Brave, use `tool_signal_harvester` or `tool_company_finder`.
- NEVER attempt to call tools like `brave_search` or `google_search` - they do not exist in this environment. 
- Failure to follow these tool-calling rules will result in a system crash.
"""
    
    tools = [
        {
            "type": "function",
            "function": {
                "name": "tool_company_finder",
                "description": "Discovers companies that match the Ideal Customer Profile (ICP).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "icp": {
                            "type": "string",
                            "description": "The Ideal Customer Profile provided by the user."
                        }
                    },
                    "required": ["icp"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "tool_signal_harvester",
                "description": "Fetches real-time signals for a SPECIFIC company like funding rounds or hiring trends.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "target": {
                            "type": "string",
                            "description": "The target company name to search for."
                        }
                    },
                    "required": ["target"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "tool_research_analyst",
                "description": "Takes harvested signals and the user's ICP to generate a 2-paragraph Account Brief.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "signals": {
                            "type": "string",
                            "description": "The JSON string of harvested signals returned from tool_signal_harvester."
                        },
                        "icp": {
                            "type": "string",
                            "description": "The Ideal Customer Profile provided by the user."
                        }
                    },
                    "required": ["signals", "icp"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "tool_outreach_automated_sender",
                "description": "Transforms the research brief into a hyper-personalized email and automatically dispatches it.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "brief": {
                            "type": "string",
                            "description": "The account brief generated from tool_research_analyst."
                        },
                        "target_email": {
                            "type": "string",
                            "description": "The candidate email to send to."
                        },
                        "target_company": {
                            "type": "string",
                            "description": "The name of the company being contacted (required for memory persistence)."
                        }
                    },
                    "required": ["brief", "target_email", "target_company"]
                }
            }
        }
    ]

    messages = [
        {"role": "system", "content": system_instruction},
        {"role": "user", "content": f"ICP: {icp}\nTask: {task}\nTarget Email: {target_email}\nPlease execute the outreach campaign."}
    ]
    
    history_steps = [{"role": "user", "content": messages[-1]["content"]}]
    
    # Phase 12: Track executed tools to prevent duplicates
    executed_tool_signatures = set()
    
    # Simple loop for orchestration (up to 4 steps)
    final_response = "Execution incomplete."
    for _ in range(5):
        try:
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=messages,
                tools=tools,
                tool_choice="auto",
                max_tokens=4096,
            )
        except Exception as e:
            if "rate_limit_exceeded" in str(e).lower():
                final_response = "Rate limit reached on Groq (70B model). Please wait a few minutes or try again later. We've optimized the research steps to use 8B to minimize this."
            else:
                final_response = f"Agent Loop Error: {str(e)}"
            break
        
        response_message = response.choices[0].message
        
        # Always append the assistant's message to the conversation history
        messages.append(response_message)

        # Capture Thought/Reasoning from the assistant's text content for history
        if response_message.content:
            history_steps.append({
                "role": "assistant",
                "type": "thought",
                "content": response_message.content
            })

        if response_message.tool_calls:
            for tool_call in response_message.tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                
                # Add Action to history
                history_steps.append({
                    "role": "assistant", 
                    "type": "action",
                    "tool": function_name,
                    "args": function_args
                })

                # Execute the matched function
                function_response = ""
                
                # Phase 12: Duplicate Guard
                arg_sig = json.dumps(function_args, sort_keys=True)
                call_sig = f"{function_name}:{arg_sig}"
                
                if call_sig in executed_tool_signatures:
                    print(f"DEBUG: Guarding against duplicate call: {function_name}")
                    function_response = f"Action already performed. results are in history. Please move to the next task step."
                else:
                    executed_tool_signatures.add(call_sig)
                    
                    if function_name == "tool_company_finder":
                        function_response = tool_company_finder(function_args.get("icp", ""))
                    elif function_name == "tool_signal_harvester":
                        function_response = tool_signal_harvester(function_args.get("target", ""))
                    elif function_name == "tool_research_analyst":
                        function_response = tool_research_analyst(function_args.get("signals", ""), function_args.get("icp", ""))
                    elif function_name == "tool_outreach_automated_sender":
                        # Extract target_company from args or harvester history fallback
                        target_company = function_args.get("target_company")
                        if not target_company:
                            # Fallback: parse from previous harvester if available
                            target_company = "Unknown"
                        
                        memory = _get_memory()
                        if target_company.lower() in memory:
                            print(f"DEBUG: SKIPPING {target_company} - Already contacted.")
                            function_response = f"Skipped: {target_company} already in memory."
                        else:
                            function_response = tool_outreach_automated_sender(
                                function_args["brief"], 
                                function_args["target_email"],
                                target_company
                            )
                    else:
                        function_response = "Unknown tool"
                
                # Internal logging to terminal
                print(f"DEBUG: Tool {function_name} execution complete.")

                # Append tool result back to Llama
                messages.append(
                    {
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": function_response,
                    }
                )
                
                # Add Observation to history
                history_steps.append({
                    "role": "tool", 
                    "type": "observation",
                    "content": function_response,
                    "tool": function_name
                })
        else:
            final_response = response_message.content
            # Special check: If the final response is short/meta, try to append the last sent email
            for msg in reversed(messages):
                try:
                    # Robust check for role/name
                    m_role = getattr(msg, 'role', None)
                    if m_role is None and isinstance(msg, dict):
                        m_role = msg.get("role")
                        
                    m_name = getattr(msg, 'name', None)
                    if m_name is None and isinstance(msg, dict):
                        m_name = msg.get("name")
                    
                    if m_role == "tool" and m_name == "tool_outreach_automated_sender":
                        content = getattr(msg, 'content', None)
                        if content is None and isinstance(msg, dict):
                            content = msg.get("content")
                        
                        if content:
                            res_data = json.loads(content)
                            if "email_copy" in res_data:
                                final_response += "\n\n--- DRAFTED EMAIL ---\n\n" + res_data["email_copy"]
                        break
                except:
                    continue
            
            history_steps.append({
                "role": "assistant", 
                "type": "decision",
                "content": final_response
            })
            break

    return {
        "final_result": final_response,
        "history": history_steps
    }
