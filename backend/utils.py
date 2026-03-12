import os
import json

# Shared file paths
STATS_FILE = os.path.join(os.path.dirname(__file__), "stats.json")
MEMORY_FILE = os.path.join(os.path.dirname(__file__), "memory.json")

def _update_stats(category: str, increment: int = 1):
    try:
        if not os.path.exists(STATS_FILE):
            with open(STATS_FILE, "w") as f:
                json.dump({"signals_detected": 0, "emails_generated": 0, "emails_sent": 0}, f)
        
        with open(STATS_FILE, "r") as f:
            stats = json.load(f)
        
        stats[category] = stats.get(category, 0) + increment
        
        with open(STATS_FILE, "w") as f:
            json.dump(stats, f, indent=4)
    except Exception as e:
        print(f"DEBUG: Failed to update stats: {e}")

def _get_memory():
    if not os.path.exists(MEMORY_FILE):
        return {}
    with open(MEMORY_FILE, "r") as f:
        return json.load(f)

def _update_memory(company: str, status: str = "contacted"):
    memory = _get_memory()
    memory[company.lower()] = status
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory, f, indent=4)

