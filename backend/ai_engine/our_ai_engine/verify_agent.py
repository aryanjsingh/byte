from agent import app
from langchain_core.messages import HumanMessage
import os

def test_agent_routing():
    print("Testing Agent Routing...")

    # Check for critical API key for LLM
    if not os.getenv("GOOGLE_API_KEY"):
        print("Skipping agent test due to missing GOOGLE_API_KEY.")
        return

    # Query 1: IP Check (Should route to GreyNoise/Shodan)
    print("\n--- Test Query: IP Check ---")
    inputs = {"messages": [HumanMessage(content="Check if IP 8.8.8.8 is malicious.")]}
    try:
        # We just want to see if it calls a tool or responds.
        for event in app.stream(inputs):
            for value in event.values():
                msg = value["messages"][-1]
                if msg.type == "ai" and msg.tool_calls:
                    print(f"Agent decided to call: {msg.tool_calls}")
                elif msg.type == "ai":
                    print(f"Final Answer Preview: {msg.content[:100]}...")
    except Exception as e:
        print(f"Agent execution failed: {e}")

    # Query 2: RAG Check
    print("\n--- Test Query: RAG Check ---")
    inputs = {"messages": [HumanMessage(content="What does NIST say about identify function?")]}
    try:
        for event in app.stream(inputs):
             for value in event.values():
                msg = value["messages"][-1]
                if msg.type == "ai" and msg.tool_calls:
                    print(f"Agent decided to call: {msg.tool_calls}")
                elif msg.type == "ai":
                    print(f"Final Answer Preview: {msg.content[:100]}...")
    except Exception as e:
        print(f"Agent execution failed: {e}")

if __name__ == "__main__":
    test_agent_routing()
