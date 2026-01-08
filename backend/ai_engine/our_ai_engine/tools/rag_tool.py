from langchain_core.tools import tool
from backend.ai_engine.kb_engine.kb_engine import query_rag

@tool
def risk_management_framework_query(query: str) -> str:
    """
    Useful for answering questions about cybersecurity standards, frameworks (NIST, CERT), 
    policies, compliance, and best practices. 
    Use this tool when the user asks for general guidance rather than specific IOC analysis.
    """
    try:
        results = query_rag(query)
        if isinstance(results, list):
            return "\n\n".join(results)
        return str(results)
    except Exception as e:
        return f"Error retrieving best practices: {str(e)}"
