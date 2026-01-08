from typing import Annotated, Literal, TypedDict
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.graph.message import add_messages
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, BaseMessage, ToolMessage
from sqlmodel import Session, select

# Internal Imports
from backend.ai_engine.our_ai_engine.tools import (
    virustotal_scan, 
    greynoise_ip_check, 
    risk_management_framework_query,
    update_user_security_profile
)
from backend.ai_engine.kb_engine.kb_engine import query_rag
from backend.database import engine
from backend.models import User, UserSecurityProfile

import os
from dotenv import load_dotenv

load_dotenv()

# --- Configuration ---
# Gemini 2.5 Pro Configuration with Thinking and Streaming
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-lite",
    temperature=0.7,
    streaming=True,  # Enable streaming for real-time responses
    # Thinking configuration for Gemini 2.5 Pro
    # Note: LangChain's ChatGoogleGenerativeAI may not directly support thinking config
    # We'll handle this at the API level if needed
)
print("🔥 DEBUG: Agent LLM Initialized with gemini-2.5-pro")



tools = [
    virustotal_scan, 
    greynoise_ip_check, 
    # risk_management_framework_query,  # RAG tool disabled as per user request
    update_user_security_profile
]
llm_with_tools = llm.bind_tools(tools)

# --- State Definition ---
class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    user_id: str # Passed from API
    profile_summary: str # Fetched from DB
    mode: str # "simple" or "turbo" - response complexity mode

# --- Nodes ---

def retrieve_context(state: AgentState):
    """
    Fetches User Profile to personalize the System Prompt.
    RAG is now available as a tool that the AI can choose to use.
    """
    user_id = state.get("user_id")
    mode = state.get("mode", "simple")  # Default to simple mode
    
    # DEBUG: Print mode to verify it's being received
    print(f"🔥 DEBUG: retrieve_context called with mode = '{mode}'")
    print(f"🔥 DEBUG: user_id = '{user_id}'")

    # Fetch Profile
    profile_text = "Standard User"
    if user_id:
        with Session(engine) as session:
            # Assuming user_id is passed as string email or int ID. 
            # API passes 'secure_user' or actual ID? 
            # In server.py we didn't pass ID yet, we need to fix server.py to pass ID.
            # let's assume it's email or ID. For now safe fail.
            try:
                if user_id.isdigit():
                    statement = select(User).where(User.id == int(user_id))
                    user = session.exec(statement).first()
                    if user and user.profile:
                        p = user.profile
                        profile_text = f"""
                        Technical Level: {p.technical_level}
                        Common Threats: {', '.join(p.common_threats) if p.common_threats else 'None'}
                        Explanation Preference: {p.explanation_preference}
                        """
            except:
                pass

    # Select system prompt based on mode - HARD SPLIT
    if mode == "turbo":
        system_prompt = f"""You are BYTE in TURBO MODE.
You are a technical cybersecurity expert, but you are also a capable general assistant.

USER ID: {user_id}
USER PROFILE: {profile_text}

### INSTRUCTIONS:
1. **Cybersecurity Topics**: Be technical, detailed, and precise. Use standard terminology.
2. **General Topics (History, Cooking, etc.)**: Answer them competently and professionally. 
   - **CRITICAL TWIST**: After answering a general question, ALWAYS try to add a specific "Cybersecurity Angle" or risk assessment related to that topic if possible.
   - Example: If asked about "Coffee", answer what it is, then add: "Security Note: Public coffeeshops often have insecure Wi-Fi. Use a VPN."

### FORMATTING:
- **LINK FORMATTING**: Never show raw long URLs. Use `[Input](url)` for the target of a scan and `[VirusTotal](url)` for reports.
- **Style**: Professional, concise, efficient.
- **FORBIDDEN**: Do not use "simple" analogies unless requested.
- **LINE BREAKS**: After every sentence ending with a period (.), start a new line.
- **SECURITY TIPS**: When providing security tips or warnings, format them as a blockquote using `> ` prefix. Example: `> Security Tip: Always use strong passwords.`

TOOLS: virustotal_scan, greynoise_ip_check, update_user_security_profile
"""
    else:  # Simple mode (default)
        system_prompt = f"""You are BYTE in SIMPLE MODE.
You are a friendly helper for non-technical Indian users. You can talk about ANYTHING (Cybersecurity OR General Life).

USER ID: {user_id}
USER PROFILE: {profile_text}

### CRITICAL INSTRUCTIONS:
1. **General Topics**: You can answer questions about cooking, movies, history, etc.
   - **THE TWIST**: Whenever you answer a general question, try to end with a fun "Byte Security Tip" related to it.
   - Example: "To make tea, boil water... Tip: Just like you don't take tea from strangers, don't take file downloads from unknown emails!"

2. **Cybersecurity Topics**: Use real-life analogies (Lock and Key, Watchman).
   - **FORBIDDEN**: Do not use complex jargon like "TCP/IP" or "Gateway" without explaining it as a "road" or "postman".

### LINK FORMATTING:
- Use **[Input](url)** (with double stars) for the address you checked.
- Use **[VirusTotal](url)** for the report.

### RESPONSE STYLE:
- Keep it simple, friendly, and relatable to Indian context (WhatsApp, UPI, Mom/Dad metaphors).
- If it's a tool result, just say if it's safe or not in 2 sentences.
- **LINE BREAKS**: After every sentence ending with a period (.), start a new line.
- **SECURITY TIPS**: When providing "Byte Security Tip" or any security advice, format it as a blockquote using `> ` prefix. Example: `> Byte Security Tip: Just like you don't take tea from strangers, don't download files from unknown emails!`
"""
    
    return {"messages": [SystemMessage(content=system_prompt)]}

def reasoner(state: AgentState):
    messages = state["messages"]
    mode = state.get("mode", "simple")
    
    # HARD SPLIT: Only send the LATEST system message and the conversation history
    # This prevents the AI from being confused by old mode instructions
    current_system_msg = None
    for msg in reversed(messages):
        if isinstance(msg, SystemMessage):
            current_system_msg = msg
            break
            
    # Filter out all other system messages from the history
    history_msgs = [m for m in messages if not isinstance(m, SystemMessage)]
    
    # Final prompt: [Current Mode System Msg] + [Conversation History]
    final_messages = ([current_system_msg] if current_system_msg else []) + history_msgs
    
    # DEBUG: Verify we have messages
    if not final_messages:
        print("⚠️ WARNING: final_messages is EMPTY. Adding fallback.")
        final_messages = [SystemMessage(content="You are BYTE."), HumanMessage(content="Hello")]

    # Handle Tool Info for Simple Mode
    try:
        if len(final_messages) > 0 and isinstance(final_messages[-1], ToolMessage) and mode == "simple":
            reminder = SystemMessage(content="REWRITE the above result simply. DO NOT use the [Simple Name/How it works] schema. Just tell the user if the link is safe or not. Use **[Input](url)** for the link and **[VirusTotal](url)** for the report. 2 sentences max.")
            response = llm_with_tools.invoke(final_messages + [reminder])
        else:
            response = llm_with_tools.invoke(final_messages)
            
        # Extract thinking/thoughts from response if present
        # Gemini 2.5 Pro may include thoughts in additional_kwargs or response_metadata
        thinking_text = ""
        if hasattr(response, 'response_metadata'):
            metadata = response.response_metadata
            # Check for thoughts in metadata
            if 'thoughts' in metadata:
                thinking_text = metadata['thoughts']
            elif 'thinking' in metadata:
                thinking_text = metadata['thinking']
        
        # Also check additional_kwargs as some versions might store it there
        if hasattr(response, 'additional_kwargs'):
            kwargs = response.additional_kwargs
            if 'thoughts' in kwargs:
                thinking_text = kwargs['thoughts']
            elif 'thinking' in kwargs:
                thinking_text = kwargs['thinking']
        
        # If we found thinking content, add it to the response
        if thinking_text and not response.additional_kwargs.get('thoughts'):
            response.additional_kwargs['thoughts'] = thinking_text
            
        # SAFETY: If Gemini returns empty, provide a fallback to avoid LangGraph error
        if not response.content and not response.tool_calls:
            print("⚠️ WARNING: AI returned EMPTY content. Using safety fallback.")
            from langchain_core.messages import AIMessage
            response = AIMessage(content="I'm sorry, I couldn't process that. Could you please try again?")
            
    except Exception as e:
        print(f"❌ LLM ERROR: {e}")
        from langchain_core.messages import AIMessage
        response = AIMessage(content="I encountered a technical glitch while thinking. Let me try again!")
        
    return {"messages": [response]}

# --- Graph ---
workflow = StateGraph(AgentState)

workflow.add_node("context_retriever", retrieve_context)
workflow.add_node("agent", reasoner)
workflow.add_node("tools", ToolNode(tools))

workflow.add_edge(START, "context_retriever")
workflow.add_edge("context_retriever", "agent")
workflow.add_conditional_edges("agent", tools_condition)
workflow.add_edge("tools", "agent")

from langgraph.checkpoint.memory import MemorySaver
memory = MemorySaver()
app = workflow.compile(checkpointer=memory)
