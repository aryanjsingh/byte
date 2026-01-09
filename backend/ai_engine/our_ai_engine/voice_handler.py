"""
Platform-agnostic Voice Handler
Automatically detects platform and uses appropriate STT engine:
- Apple Silicon (M1/M2/M3): lightning-whisper-mlx (optimized)
- x86_64 (Intel/AMD): faster-whisper (CPU optimized)
"""

import os
import sys
import platform
import base64
import tempfile

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(current_dir, "../../../")))

# Platform detection
ARCH = platform.machine()
IS_APPLE_SILICON = ARCH == "arm64" and platform.system() == "Darwin"

# Try to import appropriate Whisper implementation
STT_ENGINE = None
if IS_APPLE_SILICON:
    try:
        from lightning_whisper_mlx import LightningWhisperMLX
        STT_ENGINE = "lightning-whisper-mlx"
        print("🍎 Using Lightning Whisper MLX (Apple Silicon optimized)")
    except ImportError:
        print("⚠️  lightning-whisper-mlx not available, falling back to faster-whisper")

if not STT_ENGINE:
    try:
        from faster_whisper import WhisperModel
        STT_ENGINE = "faster-whisper"
        print("🖥️  Using Faster Whisper (x86_64/CPU optimized)")
    except ImportError:
        try:
            import whisper
            STT_ENGINE = "openai-whisper"
            print("🔊 Using OpenAI Whisper (fallback)")
        except ImportError:
            STT_ENGINE = None
            print("❌ No Whisper implementation found. Install one of:")
            print("   - lightning-whisper-mlx (Apple Silicon)")
            print("   - faster-whisper (x86_64)")
            print("   - openai-whisper (fallback)")

# Import Piper TTS
try:
    from piper import PiperVoice
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False
    print("⚠️  Piper TTS not available. Install: pip install piper-tts")


class VoiceWebHandler:
    """Platform-agnostic voice handler with automatic engine selection"""
    
    def __init__(self):
        """Initialize STT and TTS engines based on platform"""
        self.stt_engine = STT_ENGINE
        self.stt_model = None
        self.tts_voice = None
        
        # Initialize STT
        if not STT_ENGINE:
            print("❌ Voice handler initialization failed: No STT engine available")
            raise ImportError("No Whisper implementation available")
        
        print(f"Initializing {STT_ENGINE} for speech recognition...")
        self._init_stt()
        
        # Initialize TTS
        if TTS_AVAILABLE:
            print("Initializing Piper TTS...")
            self._init_tts()
        else:
            print("⚠️  TTS not available")
    
    def _init_stt(self):
        """Initialize Speech-to-Text engine based on platform"""
        if self.stt_engine == "lightning-whisper-mlx":
            # Apple Silicon - MLX optimized
            from lightning_whisper_mlx import LightningWhisperMLX
            self.stt_model = LightningWhisperMLX(model="base", batch_size=4)
            
        elif self.stt_engine == "faster-whisper":
            # x86_64 - CPU/GPU optimized
            from faster_whisper import WhisperModel
            # Use CPU for now, can be changed to "cuda" if GPU available
            self.stt_model = WhisperModel("base", device="cpu", compute_type="int8")
            
        elif self.stt_engine == "openai-whisper":
            # Fallback - standard OpenAI Whisper
            import whisper
            self.stt_model = whisper.load_model("base")
    
    def _init_tts(self):
        """Initialize Text-to-Speech engine"""
        # Resolve model path
        piper_model_path = os.path.join(
            current_dir, 
            "../kb_engine/voice_engine/models/piper/en_US-lessac-medium.onnx"
        )
        
        if os.path.exists(piper_model_path):
            self.tts_voice = PiperVoice.load(piper_model_path)
            print(f"✅ Piper model loaded: {piper_model_path}")
        else:
            print(f"⚠️  Piper model not found at {piper_model_path}")
            print("   Run setup_voice_engine.sh to download the model")
            self.tts_voice = None
    
    def transcribe_audio(self, audio_content: bytes) -> str:
        """
        Transcribes audio bytes to text using platform-appropriate engine.
        
        Args:
            audio_content: Raw audio bytes
            
        Returns:
            Transcribed text string
        """
        if not self.stt_model:
            print("❌ STT model not initialized")
            return ""
        
        import subprocess
        
        # 1. Save raw audio
        with tempfile.NamedTemporaryFile(suffix=".raw", delete=False) as raw_tmp:
            raw_tmp.write(audio_content)
            raw_path = raw_tmp.name
        
        # 2. Convert to WAV format (16kHz, mono, pcm_s16le)
        wav_path = raw_path + ".wav"
        try:
            # Standard conversion for all Whisper implementations
            cmd = [
                "ffmpeg", "-y", "-i", raw_path,
                "-ar", "16000",  # 16kHz sample rate
                "-ac", "1",      # Mono
                "-acodec", "pcm_s16le",
                wav_path
            ]
            
            result = subprocess.run(cmd, check=False, capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"FFmpeg conversion failed: {result.stderr}")
                # Try simpler conversion
                cmd = ["ffmpeg", "-y", "-i", raw_path, "-ar", "16000", "-ac", "1", wav_path]
                result = subprocess.run(cmd, check=False, capture_output=True, text=True)
                if result.returncode != 0:
                    raise Exception("FFmpeg conversion failed")
            
            # Get audio duration
            wav_size = os.path.getsize(wav_path)
            duration_cmd = [
                "ffprobe", "-v", "error", 
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1", 
                wav_path
            ]
            duration_result = subprocess.run(duration_cmd, capture_output=True, text=True)
            duration = float(duration_result.stdout.strip()) if duration_result.returncode == 0 else 0.0
            
            print(f"🎤 Audio converted: {wav_size} bytes, {duration:.2f}s")
            
            # Validate minimum duration
            if duration < 0.5:
                print(f"⚠️  Audio too short ({duration:.2f}s)")
                return ""
            
            # 3. Transcribe using appropriate engine
            text = self._transcribe_with_engine(wav_path)
            return text
            
        except Exception as e:
            print(f"❌ Transcription error: {e}")
            import traceback
            traceback.print_exc()
            return ""
        finally:
            # Cleanup
            for p in [raw_path, wav_path]:
                if os.path.exists(p):
                    try:
                        os.remove(p)
                    except:
                        pass
    
    def _transcribe_with_engine(self, audio_path: str) -> str:
        """Transcribe audio using the appropriate engine"""
        try:
            if self.stt_engine == "lightning-whisper-mlx":
                # Lightning Whisper MLX
                result = self.stt_model.transcribe(audio_path)
                text = result.get("text", "").strip() if result else ""
                
            elif self.stt_engine == "faster-whisper":
                # Faster Whisper - returns segments
                segments, info = self.stt_model.transcribe(audio_path)
                text = " ".join([segment.text for segment in segments]).strip()
                
            elif self.stt_engine == "openai-whisper":
                # OpenAI Whisper
                result = self.stt_model.transcribe(audio_path)
                text = result.get("text", "").strip() if result else ""
            else:
                text = ""
            
            print(f"📝 Transcribed: '{text}'")
            return text
            
        except Exception as e:
            print(f"❌ Engine transcription error: {e}")
            return ""
    
    def synthesize_speech(self, text: str) -> str:
        """
        Synthesizes text to speech and returns base64 encoded audio.
        
        Args:
            text: Text to synthesize
            
        Returns:
            Base64 encoded WAV audio string
        """
        if not self.tts_voice:
            print("❌ TTS not available")
            return None
        
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            import wave
            import re
            
            # Clean text for TTS
            clean_text = self._clean_text_for_tts(text)
            
            if not clean_text:
                clean_text = "Audio response unavailable."
            
            # Synthesize
            with wave.open(tmp_path, "wb") as wav_file:
                self.tts_voice.synthesize_wav(clean_text, wav_file)
            
            # Read and encode
            with open(tmp_path, "rb") as f:
                audio_data = f.read()
            
            return base64.b64encode(audio_data).decode("utf-8")
            
        except Exception as e:
            print(f"❌ TTS error: {e}")
            return None
        finally:
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except:
                    pass
    
    def _clean_text_for_tts(self, text: str) -> str:
        """Clean text for TTS by removing markdown, URLs, etc."""
        import re
        
        # Remove markdown links [text](url) -> text
        clean = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
        
        # Remove URLs
        clean = re.sub(
            r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',
            '', 
            clean
        )
        
        # Remove markdown formatting
        clean = re.sub(r'[*_`]', '', clean)
        
        # Remove list markers
        clean = re.sub(r'\s-\s', ' ', clean)
        clean = re.sub(r'^\s*-\s', '', clean, flags=re.MULTILINE)
        
        # Remove emojis
        clean = re.sub(r'[\U00010000-\U0010ffff]', '', clean)
        
        # Collapse whitespace
        clean = re.sub(r'\s+', ' ', clean).strip()
        
        return clean


# Platform detection helper
def get_platform_info():
    """Get platform information for debugging"""
    return {
        "architecture": ARCH,
        "system": platform.system(),
        "is_apple_silicon": IS_APPLE_SILICON,
        "stt_engine": STT_ENGINE,
        "tts_available": TTS_AVAILABLE
    }


if __name__ == "__main__":
    # Test the voice handler
    print("=" * 60)
    print("Voice Handler Platform Detection")
    print("=" * 60)
    
    info = get_platform_info()
    for key, value in info.items():
        print(f"{key}: {value}")
    
    print("\nAttempting to initialize voice handler...")
    try:
        handler = VoiceWebHandler()
        print("✅ Voice handler initialized successfully!")
    except Exception as e:
        print(f"❌ Failed to initialize: {e}")
