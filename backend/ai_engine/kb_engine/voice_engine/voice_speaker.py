import os
import wave
import sys
from piper import PiperVoice

class VoiceSpeaker:
    def __init__(self, model_path="models/piper/en_US-lessac-medium.onnx"):
        # Ensure path is absolute for reliability
        current_dir = os.path.dirname(os.path.abspath(__file__))
        if not os.path.isabs(model_path):
            model_path = os.path.join(current_dir, model_path)
            
        print(f"Initializing Piper TTS with model: {model_path}")
        
        if not os.path.exists(model_path):
            print(f"Error: Piper model not found at {model_path}")
            # Fallback or initialization error
            self.voice = None
            return

        try:
            self.voice = PiperVoice.load(model_path)
            self.output_file = os.path.join(current_dir, "response_output.wav")
        except Exception as e:
            print(f"Failed to load Piper model: {e}")
            self.voice = None

    def speak(self, text):
        """
        Synthesizes text to a WAV file and plays it using native macOS 'afplay'.
        """
        if not self.voice:
            print("Piper TTS not initialized correctly.")
            return

        print(f"Speaking: {text}")
        try:
            # Generate speech to file
            with wave.open(self.output_file, "wb") as wav_file:
                self.voice.synthesize_wav(text, wav_file)
            
            # Play using macOS native utility
            os.system(f"afplay {self.output_file}")
            
        except Exception as e:
            print(f"Error in Piper TTS: {e}")

    def stop(self):
        # Kill the afplay process if needed.
        os.system("killall afplay > /dev/null 2>&1")

if __name__ == "__main__":
    speaker = VoiceSpeaker()
    speaker.speak("Piper engine online. Security assistant ready.")

