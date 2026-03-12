import os

KNOWLEDGE_DIR = os.path.join(os.path.dirname(__file__), "knowledge_base")

def get_rag_context(target_company: str) -> str:
    """
    Scans the knowledge_base directory for any text files mentioning the target_company
    or provide general product knowledge.
    """
    context = []
    
    if not os.path.exists(KNOWLEDGE_DIR):
        return ""

    # 1. Search for company-specific notes
    # 2. Search for general case studies/product info
    for filename in os.listdir(KNOWLEDGE_DIR):
        if filename.endswith(".txt") or filename.endswith(".md"):
            with open(os.path.join(KNOWLEDGE_DIR, filename), "r") as f:
                content = f.read()
                # Simple heuristic: if company mentioned or if it's a general 'product' file
                if target_company.lower() in content.lower() or "product" in filename.lower():
                    context.append(f"--- From {filename} ---\n{content}")

    return "\n\n".join(context)
