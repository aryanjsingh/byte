import sys
import os

# Ensure project root is in path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from backend.ai_engine.our_ai_engine.agent import app
from langchain_core.messages import HumanMessage

def main():
    print("Initializing Cybersecurity Agent...")
    if not os.getenv("GOOGLE_API_KEY"):
         print("Warning: GOOGLE_API_KEY not set in environment.")

    print("\n--- Cybersecurity Chatbot (Type 'quit' to exit) ---")
    print("Ask about IPs, URLs, files, or security standards (NIST/CERT).")

    while True:
        try:
            user_input = input("\n> ")
            if user_input.lower() in ["quit", "exit"]:
                break
            
            # Simple streaming or invoke
            initial_state = {"messages": [HumanMessage(content=user_input)]}
            
            # We can stream events to show tool usage
            final_response = None
            print("\nProcessing...", end="", flush=True)
            
            for event in app.stream(initial_state):
                for value in event.values():
                    # value is the state update
                    msg = value["messages"][-1]
                    if msg.type == "ai" and msg.tool_calls:
                         print(f"\n[Agent] Calling tools: {[tc['name'] for tc in msg.tool_calls]}...")
                    elif msg.type == "tool":
                         print(f"\n[Tool] Result received.")
                    elif msg.type == "ai":
                         final_response = msg.content
            
            print(f"\n\n{final_response}")

        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"\nError: {e}")

if __name__ == "__main__":
    main()
