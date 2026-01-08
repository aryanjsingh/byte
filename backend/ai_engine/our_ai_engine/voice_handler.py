import os
import sys
import uuid
import base64
import tempfile
from lightning_whisper_mlx import LightningWhisperMLX
from piper import PiperVoice

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(current_dir, "../../../")))

class VoiceWebHandler:
    def __init__(self):
        # Initialize Whisper (STT)
        print("Initializing Whisper engine for Web...")
        self.stt_model = LightningWhisperMLX(model="base", batch_size=4)
        
        # Initialize Piper (TTS)
        print("Initializing Piper engine for Web...")
        # Resolve model path
        piper_model_path = os.path.join(current_dir, "../kb_engine/voice_engine/models/piper/en_US-lessac-medium.onnx")
        if os.path.exists(piper_model_path):
            self.tts_voice = PiperVoice.load(piper_model_path)
        else:
            print(f"Warning: Piper model not found at {piper_model_path}")
            self.tts_voice = None

    def transcribe_audio(self, audio_content: bytes):
        """Transcribes bytes content to text with robust conversion."""
        import subprocess
        import wave
        
        # 1. Save raw received audio
        with tempfile.NamedTemporaryFile(suffix=".raw", delete=False) as raw_tmp:
            raw_tmp.write(audio_content)
            raw_path = raw_tmp.name
        
        # 2. Convert to standard 16kHz mono WAV for Whisper with audio enhancement
        wav_path = raw_path + ".wav"
        try:
            # Standard ffmpeg conversion:
            # - Ensure 16kHz sample rate (Whisper requirement)
            # - Mono channel
            # - pcm_s16le encoding
            cmd = [
                "ffmpeg", "-y", "-i", raw_path,
                "-ar", "16000",
                "-ac", "1",
                "-acodec", "pcm_s16le",
                wav_path
            ]
            
            result_subprocess = subprocess.run(cmd, check=False, capture_output=True, text=True)
            if result_subprocess.returncode != 0:
                print(f"FFmpeg failed for input file: {raw_path} -> output: {wav_path}")
                print(f"Stderr details: {result_subprocess.stderr}")
                # Try simpler conversion without filters
                cmd_simple = ["ffmpeg", "-y", "-i", raw_path, "-ar", "16000", "-ac", "1", wav_path]
                result_simple = subprocess.run(cmd_simple, check=False, capture_output=True, text=True)
                if result_simple.returncode != 0:
                    print(f"Simple FFmpeg conversion also failed: {result_simple.stderr}")
                    raise Exception("FFmpeg conversion failed")
            
            # Check wav file size and duration
            wav_size = os.path.getsize(wav_path)
            
            # Get audio duration using ffprobe
            duration_cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", 
                          "-of", "default=noprint_wrappers=1:nokey=1", wav_path]
            duration_result = subprocess.run(duration_cmd, capture_output=True, text=True)
            duration = float(duration_result.stdout.strip()) if duration_result.returncode == 0 else 0.0
            
            print(f"DEBUG: FFmpeg conversion successful. Wav file: {wav_path}, Size: {wav_size} bytes, Duration: {duration:.2f}s")
            
            # Validate minimum duration (at least 0.5 seconds)
            if duration < 0.5:
                print(f"WARNING: Audio too short ({duration:.2f}s), may not contain speech")
                return ""
            
            # 3. Transcribe
            result = self.stt_model.transcribe(wav_path)
            print(f"DEBUG: Raw Whisper result: {result}")
            
            if result:
                text = result.get("text", "").strip()
                print(f"DEBUG: Extracted text: '{text}' (length: {len(text)})")
                
                # Additional validation: check if text is meaningful
                if not text or len(text) < 2:
                    # Check segments for any non-empty text
                    segments = result.get("segments", [])
                    if segments:
                        segment_texts = [seg[2] if len(seg) > 2 else "" for seg in segments]
                        combined = " ".join([s for s in segment_texts if s]).strip()
                        if combined:
                            print(f"DEBUG: Found text in segments: '{combined}'")
                            return combined
                    print("DEBUG: Whisper returned empty or very short text")
                    return ""
                
                return text
            return ""
        except Exception as e:
            print(f"STT/FFmpeg Error: {e}")
            import traceback
            traceback.print_exc()
            # Try transcribing raw if conversion fails
            try:
                result = self.stt_model.transcribe(raw_path)
                return result.get("text", "").strip() if result else ""
            except Exception as e2:
                print(f"Raw transcription also failed: {e2}")
                return ""
        finally:
            # Cleanup
            for p in [raw_path, wav_path]:
                if os.path.exists(p):
                    try:
                        os.remove(p)
                    except:
                        pass

    def synthesize_speech(self, text: str):
        """Synthesizes text to base64 encoded audio."""
        if not self.tts_voice:
            return None
            
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_path = tmp.name
            
        try:
            import wave
            import re

            # Clean text for TTS
            # 1. Remove markdown links [text](url) -> text
            clean_text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
            # 2. Remove URLs
            clean_text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', clean_text)
            # 3. Remove bold/italic/code markers
            clean_text = re.sub(r'[*_`]', '', clean_text)
            # 4. Remove specific annoyance: " - " or leading "- "
            clean_text = re.sub(r'\s-\s', ' ', clean_text)
            clean_text = re.sub(r'^\s*-\s', '', clean_text, flags=re.MULTILINE)
            # 5. Remove Emojis (unicode ranges)
            clean_text = re.sub(r'[\U00010000-\U0010ffff]', '', clean_text)
            # 6. Collapse whitespace
            clean_text = re.sub(r'\s+', ' ', clean_text).strip()

            if not clean_text:
                clean_text = "Audio response unavailable."

            with wave.open(tmp_path, "wb") as wav_file:
                self.tts_voice.synthesize_wav(clean_text, wav_file)
            
            with open(tmp_path, "rb") as f:
                audio_data = f.read()
                
            return base64.b64encode(audio_data).decode("utf-8")
        except Exception as e:
            print(f"TTS Error: {e}")
            return None
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
