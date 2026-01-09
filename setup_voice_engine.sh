#!/bin/bash

# ==============================================================================
# BYTE Voice Engine Setup Script
# ==============================================================================
# This script installs voice recognition (STT) and text-to-speech (TTS)
# dependencies for the BYTE cybersecurity assistant.
#
# Supports:
# - Apple Silicon (M1/M2/M3) - Uses lightning-whisper-mlx
# - x86_64 (Intel/AMD) - Uses openai-whisper with faster-whisper
# - Piper TTS for both architectures
# ==============================================================================

set -e  # Exit on error

echo "======================================================================"
echo "BYTE Voice Engine Setup"
echo "======================================================================"
echo ""

# Detect architecture
ARCH=$(uname -m)
OS=$(uname -s)

echo "📋 System Information:"
echo "   Architecture: $ARCH"
echo "   OS: $OS"
echo "   Python: $(python3 --version)"
echo ""

# Check if running on Apple Silicon
if [[ "$ARCH" == "arm64" && "$OS" == "Darwin" ]]; then
    PLATFORM="apple_silicon"
    echo "✅ Detected Apple Silicon (M1/M2/M3)"
elif [[ "$ARCH" == "x86_64" ]]; then
    PLATFORM="x86_64"
    echo "✅ Detected x86_64 (Intel/AMD)"
else
    echo "❌ Unsupported architecture: $ARCH"
    exit 1
fi

echo ""
echo "======================================================================"
echo "Step 1: Installing System Dependencies"
echo "======================================================================"

# Install system dependencies based on OS
if [[ "$OS" == "Darwin" ]]; then
    # macOS
    if ! command -v brew &> /dev/null; then
        echo "⚠️  Homebrew not found. Please install Homebrew first:"
        echo "   /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
        exit 1
    fi
    
    echo "Installing macOS dependencies..."
    brew install ffmpeg portaudio
    
elif [[ "$OS" == "Linux" ]]; then
    # Linux
    echo "Installing Linux dependencies..."
    
    # Check if running as root or has sudo
    if [[ $EUID -eq 0 ]]; then
        apt-get update
        apt-get install -y ffmpeg libportaudio2 portaudio19-dev python3-pyaudio build-essential
    else
        sudo apt-get update
        sudo apt-get install -y ffmpeg libportaudio2 portaudio19-dev python3-pyaudio build-essential
    fi
else
    echo "❌ Unsupported OS: $OS"
    exit 1
fi

echo "✅ System dependencies installed"
echo ""

echo "======================================================================"
echo "Step 2: Installing Python Voice Dependencies"
echo "======================================================================"

# Navigate to backend directory
cd "$(dirname "$0")/backend"

# Install based on platform
if [[ "$PLATFORM" == "apple_silicon" ]]; then
    echo "Installing Apple Silicon optimized packages..."
    
    # Install MLX framework
    pip3 install mlx
    
    # Install lightning-whisper-mlx (optimized for Apple Silicon)
    pip3 install lightning-whisper-mlx
    
    echo "✅ lightning-whisper-mlx installed (Apple Silicon optimized)"
    
elif [[ "$PLATFORM" == "x86_64" ]]; then
    echo "Installing x86_64 packages..."
    
    # Install faster-whisper (optimized for CPU/GPU)
    pip3 install faster-whisper
    
    # Install openai-whisper as fallback
    pip3 install openai-whisper
    
    echo "✅ faster-whisper and openai-whisper installed"
fi

# Install Piper TTS (works on all platforms)
echo ""
echo "Installing Piper TTS..."
pip3 install piper-tts

# Install additional audio processing libraries
pip3 install soundfile librosa pydub

echo "✅ All Python voice packages installed"
echo ""

echo "======================================================================"
echo "Step 3: Downloading Piper TTS Model"
echo "======================================================================"

# Create models directory
MODELS_DIR="ai_engine/kb_engine/voice_engine/models/piper"
mkdir -p "$MODELS_DIR"

# Download Piper model
PIPER_MODEL_URL="https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx"
PIPER_CONFIG_URL="https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json"

echo "Downloading Piper voice model..."
curl -L -o "$MODELS_DIR/en_US-lessac-medium.onnx" "$PIPER_MODEL_URL"
curl -L -o "$MODELS_DIR/en_US-lessac-medium.onnx.json" "$PIPER_CONFIG_URL"

echo "✅ Piper model downloaded"
echo ""

echo "======================================================================"
echo "Step 4: Updating voice_handler.py for Platform Compatibility"
echo "======================================================================"

# Create platform-aware voice handler
VOICE_HANDLER_PATH="ai_engine/our_ai_engine/voice_handler.py"

if [[ "$PLATFORM" == "x86_64" ]]; then
    echo "Updating voice handler for x86_64..."
    # We'll create a backup and update it
    cp "$VOICE_HANDLER_PATH" "$VOICE_HANDLER_PATH.backup"
    echo "✅ Backup created: $VOICE_HANDLER_PATH.backup"
    echo "⚠️  Voice handler needs manual update for x86_64 compatibility"
    echo "   See voice_handler_x86.py for x86_64 compatible version"
fi

echo ""
echo "======================================================================"
echo "Step 5: Testing Installation"
echo "======================================================================"

# Test import
python3 << EOF
import sys
sys.path.insert(0, '.')

print("Testing voice dependencies...")

# Test Piper
try:
    from piper import PiperVoice
    print("✅ Piper TTS: OK")
except ImportError as e:
    print(f"❌ Piper TTS: FAILED - {e}")
    sys.exit(1)

# Test Whisper (platform specific)
try:
    if "$PLATFORM" == "apple_silicon":
        from lightning_whisper_mlx import LightningWhisperMLX
        print("✅ Lightning Whisper MLX: OK")
    else:
        from faster_whisper import WhisperModel
        print("✅ Faster Whisper: OK")
except ImportError as e:
    print(f"❌ Whisper: FAILED - {e}")
    sys.exit(1)

# Test FFmpeg
import subprocess
try:
    result = subprocess.run(['ffmpeg', '-version'], capture_output=True)
    print("✅ FFmpeg: OK")
except FileNotFoundError:
    print("❌ FFmpeg: NOT FOUND")
    sys.exit(1)

print("\\n✅ All voice dependencies installed successfully!")
EOF

if [ $? -eq 0 ]; then
    echo ""
    echo "======================================================================"
    echo "✅ Voice Engine Setup Complete!"
    echo "======================================================================"
    echo ""
    echo "Platform: $PLATFORM"
    echo "STT Engine: $([ "$PLATFORM" == "apple_silicon" ] && echo "lightning-whisper-mlx" || echo "faster-whisper")"
    echo "TTS Engine: Piper"
    echo ""
    echo "🎤 Voice features are now enabled!"
    echo ""
    echo "To test voice features:"
    echo "  1. Restart the backend server"
    echo "  2. Use the /chat/voice endpoint"
    echo ""
    echo "Installed packages:"
    if [[ "$PLATFORM" == "apple_silicon" ]]; then
        echo "  - lightning-whisper-mlx (STT)"
    else
        echo "  - faster-whisper (STT)"
        echo "  - openai-whisper (STT fallback)"
    fi
    echo "  - piper-tts (TTS)"
    echo "  - soundfile, librosa, pydub (audio processing)"
    echo ""
else
    echo ""
    echo "======================================================================"
    echo "❌ Installation Failed"
    echo "======================================================================"
    echo ""
    echo "Please check the error messages above and try again."
    echo "You may need to install system dependencies manually."
    echo ""
    exit 1
fi
