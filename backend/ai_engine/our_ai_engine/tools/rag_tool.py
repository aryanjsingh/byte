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


@tool
def cybersecurity_knowledge_search(query: str) -> str:
    """
    Search the cybersecurity knowledge base for information about:
    - Phishing, scams, and fraud detection
    - Indian cyber laws (IT Act sections)
    - Cybercrime reporting (1930 helpline, cybercrime.gov.in)
    - UPI/payment fraud prevention
    - Incident response procedures
    - Cyber hygiene best practices
    - Mental health support for cybercrime victims
    - OWASP, NIST, CERT frameworks
    
    Use this tool when users ask about:
    - How to report cybercrime in India
    - What to do if hacked/scammed
    - Cyber laws and penalties
    - Security best practices
    - Recognizing phishing/scams
    """
    try:
        results = query_rag(query, n_results=5)
        if isinstance(results, list) and results:
            formatted = []
            for i, result in enumerate(results, 1):
                formatted.append(f"--- Result {i} ---\n{result}")
            return "\n\n".join(formatted)
        return "No relevant information found in knowledge base."
    except Exception as e:
        return f"Error searching knowledge base: {str(e)}"
