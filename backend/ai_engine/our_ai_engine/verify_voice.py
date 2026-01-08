import os
import time
import sys

def verify_modules():
    print("--- Verifying Voice Dependencies ---")
    
    # Check Imports
    try:
        import vosk
        print("[OK] vosk imported")
    except ImportError:
        print("[FAIL] vosk not found")

    try:
        import pyaudio
        print("[OK] pyaudio imported")
    except ImportError:
        print("[FAIL] pyaudio not found")

    try:
        import pyttsx3
        print("[OK] pyttsx3 imported")
    except ImportError:
        print("[FAIL] pyttsx3 not found")

    # Check Model
    model_path = "vosk-model-small-en-us-0.15"
    if os.path.exists(model_path):
         print(f"[OK] Vosk model found at {model_path}")
    else:
         print(f"[WARN] Vosk model not found (will be downloaded on first run)")

    print("\n--- Verification Instructions ---")
    print("To test the full loop, run: python voice_bridge.py")
    print("1. The system should speak 'Voice system initializing'.")
    print("2. It will download the model if missing (takes a moment).")
    print("3. When it says 'I am listening', speak into the mic.")
    print("4. Say 'hello' or 'status' to test response.")
    print("5. Say 'quit' to exit.")

if __name__ == "__main__":
    verify_modules()
