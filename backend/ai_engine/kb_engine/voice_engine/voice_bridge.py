import os
import sys

# Ensure project root is in path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../")))

from backend.ai_engine.kb_engine.voice_engine.voice_listener import VoiceListener
from backend.ai_engine.kb_engine.voice_engine.voice_speaker import VoiceSpeaker
from backend.ai_engine.our_ai_engine.agent import app
from langchain_core.messages import HumanMessage
import time

def process_security_query(text):
    """
    Passes user voice transcription to the LangGraph AI agent.
    """
    print(f"Agent processing: {text}")
    try:
        # We use a static thread_id or just call it as a one-off for now
        config = {"configurable": {"thread_id": "voice_user_1"}}
        
        # Invoke the agent
        response = app.invoke(
            {"messages": [HumanMessage(content=text)]}, 
            config=config
        )
        
        # Extract the last message content (the agent's final answer)
        final_message = response["messages"][-1].content
        
        # Clean up Markdown for TTS (optional but recommended)
        clean_text = final_message.replace("#", "").replace("*", "").replace("`", "").strip()
        
        return clean_text
        
    except Exception as e:
        return f"Agent error: {str(e)}"

def run_voice_bridge():
    print("Initializing BYTE Voice Bridge with AI Agent...")
    
    try:
        # This will download models if missing
        speaker = VoiceSpeaker()
        speaker.speak("Voice processing system online. Connection to brain established.")
        
        listener = VoiceListener()
        speaker.speak("I am ready for your security questions.")
        
        while True:
            # 1. Listen
            user_text = listener.listen()
            if not user_text or len(user_text.strip()) < 2:
                continue
                
            print(f"> User: {user_text}")
            
            if any(cmd in user_text.lower() for cmd in ["quit", "exit", "stop", "deactivate"]):
                speaker.speak("Deactivating voice module and shutting down. Goodbye.")
                break
                
            # 2. Process with AI
            response_text = process_security_query(user_text)
            print(f"> BYTE: {response_text}")
            
            # 3. Speak
            speaker.speak(response_text)
            
    except KeyboardInterrupt:
        print("\nStopping...")
        # No need to speak here as process is dying
    except Exception as e:
        print(f"System Error: {e}")
    finally:
        if 'listener' in locals():
            listener.close()

if __name__ == "__main__":
    run_voice_bridge()
