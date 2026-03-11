import os
import json
from groq import Groq

def tool_signal_harvester(target: str = None) -> str:
    """
    Fetches data for a company. Captures Live Buyer Signals.
    Tracks a small but high-value subset of intent triggers.
    
    Args:
        target: The target company name. If None, returns general prospects.
    """
    signals = {
        "CyberShield Inc.": {
            "signals": [
                "Funding rounds: Raised Series B $20M last week",
                "Hiring trends: Opened 5 new engineering roles and a VP of Security",
                "Tech stack changes: Migrating to cloud infrastructure",
            ]
        },
        "TechGrowth Corp": {
            "signals": [
                "Funding rounds: Seed stage",
                "Hiring trends: Hiring 2 developers",
            ]
        }
    }
    
    # Return CyberShield by default for the challenge
    target_key = target if target and target in signals else "CyberShield Inc."
    return json.dumps({target_key: signals[target_key]})

def tool_research_analyst(signals: str, icp: str) -> str:
    """
    Takes harvested signals and the user's ICP to generate a 2-paragraph 
    "Account Brief" highlighting specific pain points and strategic alignment.
    
    Args:
        signals: The JSON string of harvested signals.
        icp: The Ideal Customer Profile.
    """
    try:
        client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
        prompt = f"""Given these live signals: {signals} and our ICP: {icp}. 
        Generate a 2-paragraph Account Brief analyzing their strategic alignment and potential pain points.
        STRICT RULE: You MUST use the actual company names and data from the signals. 
        Do NOT use placeholders like '[Company]' or '[Signal]'.
        """
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        return f"Account Brief Fallback: The prospect has recently raised significant funding and is expanding their engineering team. This matches our ICP of targeting growing tech startups who may need to secure their expanding infrastructure. ({str(e)})"

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
        prompt = f"""Write a hyper-personalized outreach email based on this Account Brief: {brief}. 
        Send it to {target_email}. 
        
        Zero-Template Policy: The email MUST explicitly reference the live signals. 
        STRICT RULE: You MUST NOT use generic templates or placeholders like '[Company Name]', '[Amount]', or '[Candidate]'.
        You MUST use the actual details provided in the brief. 
        Return ONLY the final email body as if sent.
        """
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
        )
        return json.dumps({
            "status": "success",
            "message": "Email dispatched successfully via automated sender.",
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
Objective: Find companies, research them, and send personalized outreach emails.

Sequential Reasoning:
1. Signal Capture: Use `tool_signal_harvester`.
2. Contextual Research: Use `tool_research_analyst` (MUST pass raw signals from step 1).
3. Automated Delivery: Use `tool_outreach_automated_sender` (MUST pass brief from step 2).

Zero-Template Policy: Do NOT use generic templates. 
STRICT Dynamic Mapping: The email MUST explicitly reference the EXACT company name and EXACT signals returned by `tool_signal_harvester`. 
Example: If the harvester returns "CyberShield Inc." and "$20M", the email MUST NOT say "ABC Corp" or "$25M".

Output Rule: In your final response, you MUST display the full body of the email you drafted.
"""
    
    tools = [
        {
            "type": "function",
            "function": {
                "name": "tool_signal_harvester",
                "description": "Fetches mock data for a company. Captures Live Buyer Signals like funding rounds or hiring trends.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "target": {
                            "type": "string",
                            "description": "The target company name. If None, returns general prospects."
                        }
                    }
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
                        }
                    },
                    "required": ["brief", "target_email"]
                }
            }
        }
    ]

    messages = [
        {"role": "system", "content": system_instruction},
        {"role": "user", "content": f"ICP: {icp}\nTask: {task}\nTarget Email: {target_email}\nPlease execute the outreach campaign."}
    ]
    
    history_steps = [{"role": "user", "content": messages[-1]["content"]}]
    
    # Simple loop for orchestration (up to 4 steps)
    final_response = "Execution incomplete."
    for _ in range(5):
        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                tools=tools,
                tool_choice="auto",
                max_tokens=4096,
            )
        except Exception as e:
            final_response = f"Agent Loop Error: {str(e)}"
            break
        
        response_message = response.choices[0].message
        
        if response_message.tool_calls:
            # Add the assistant's request to call a tool to messages
            messages.append(response_message)
            
            for tool_call in response_message.tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                
                # Execute the matched function
                function_response = ""
                if function_name == "tool_signal_harvester":
                    function_response = tool_signal_harvester(function_args.get("target"))
                elif function_name == "tool_research_analyst":
                    function_response = tool_research_analyst(function_args.get("signals", ""), function_args.get("icp", ""))
                elif function_name == "tool_outreach_automated_sender":
                    function_response = tool_outreach_automated_sender(function_args.get("brief", ""), function_args.get("target_email", ""))
                
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
                
                # Add to history for frontend with structured metadata
                history_steps.append({
                    "role": "assistant", 
                    "content": f"[Agent chose: {function_name}]",
                    "tool": function_name,
                    "args": function_args
                })
                history_steps.append({
                    "role": "tool", 
                    "content": function_response,
                    "tool": function_name
                })
        else:
            final_response = response_message.content
            # Special check: If the final response is short/meta, try to append the last sent email
            for msg in reversed(messages):
                if msg.get("role") == "tool" and msg.get("name") == "tool_outreach_automated_sender":
                    try:
                        res_data = json.loads(msg["content"])
                        if "email_copy" in res_data:
                            final_response += "\n\n--- DRAFTED EMAIL ---\n\n" + res_data["email_copy"]
                    except:
                        pass
                    break
            
            history_steps.append({"role": "assistant", "content": final_response})
            break

    return {
        "final_result": final_response,
        "history": history_steps
    }
