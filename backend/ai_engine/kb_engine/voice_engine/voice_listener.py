import os
import sys
import pyaudio
import numpy as np
import wave
import tempfile
from lightning_whisper_mlx import LightningWhisperMLX

# Lightning Whisper MLX typically uses "tiny", "base", etc.
DEFAULT_MODEL = "base" 

class VoiceListener:
    def __init__(self, model=DEFAULT_MODEL, threshold=500, silence_duration=1.2):
        """
        Initializes the VoiceListener with Lightning-Whisper-MLX.
        :param model: The Whisper model name (e.g., "tiny", "base").
        :param threshold: Energy threshold to trigger speech detection.
        :param silence_duration: Seconds of silence after speech to trigger transcription.
        """
        print(f"Initializing Lightning-Whisper-MLX listener with model: {model}")
        self.model_name = model
        self.threshold = threshold
        self.silence_duration = silence_duration
        
        # Initialize Lightning Whisper
        # batch_size=4 is a good balance for real-time responsiveness
        self.whisper = LightningWhisperMLX(model=self.model_name, batch_size=4)
        
        self.chunk_size = 1024
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = 16000
        
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(format=self.format,
                                  channels=self.channels,
                                  rate=self.rate,
                                  input=True,
                                  frames_per_buffer=self.chunk_size)
        self.stream.start_stream()
        print("Microphone stream active.")

    def listen(self):
        """
        Listens until a phrase is detected followed by silence, then returns transcription.
        """
        print("Listening (Lightning-Whisper-MLX)...")
        frames = []
        silent_chunks = 0
        recording = False
        
        max_silent_chunks = int(self.silence_duration * self.rate / self.chunk_size)
        
        while True:
            try:
                data = self.stream.read(self.chunk_size, exception_on_overflow=False)
                audio_data = np.frombuffer(data, dtype=np.int16)
                
                energy = np.sqrt(np.mean(audio_data.astype(np.float32)**2))
                
                if energy > self.threshold:
                    if not recording:
                        print(">> Recording...")
                        recording = True
                    frames.append(data)
                    silent_chunks = 0
                elif recording:
                    frames.append(data)
                    silent_chunks += 1
                    if silent_chunks > max_silent_chunks:
                        print(">> Processing transcription...")
                        text = self.transcribe(frames)
                        if text:
                            return text
                        else:
                            frames = []
                            recording = False
                            silent_chunks = 0
                else:
                    pass
            except Exception as e:
                print(f"Error reading audio: {e}")
                break

    def transcribe(self, frames):
        """
        Saves frames to a temporary WAV file and transcribes with Lightning-Whisper-MLX.
        """
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
            tmp_path = tmp_file.name
            
        try:
            wf = wave.open(tmp_path, 'wb')
            wf.setnchannels(self.channels)
            wf.setsampwidth(self.p.get_sample_size(self.format))
            wf.setframerate(self.rate)
            wf.writeframes(b''.join(frames))
            wf.close()
            
            # Transcribe
            # Lightning-Whisper-MLX's transcribe returns a dictionary with a 'text' key
            result = self.whisper.transcribe(tmp_path)
            
            if result:
                text = result.get('text', '').strip()
                return text
            return ""

        except Exception as e:
            print(f"Transcription error: {e}")
            return ""
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def close(self):
        print("Closing listener.")
        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()

if __name__ == "__main__":
    listener = VoiceListener()
    try:
        while True:
            text = listener.listen()
            print(f"Heard: {text}")
            if any(cmd in text.lower() for cmd in ["quit", "exit", "stop"]):
                break
    except KeyboardInterrupt:
        pass
    finally:
        listener.close()


