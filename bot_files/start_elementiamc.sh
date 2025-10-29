#!/bin/bash

# Start script cho EleMentiaMC hosting
# Chmod +x start_elementiamc.sh để có thể chạy

echo "🚀 Starting Discord Bot on EleMentiaMC..."

# Kiểm tra Python version
python3 --version

# Kiểm tra FFmpeg
if command -v ffmpeg &> /dev/null; then
    echo "✅ FFmpeg found: $(ffmpeg -version | head -n1)"
    USE_FFMPEG=true
else
    echo "⚠️ FFmpeg not found - using simple music mode"
    USE_FFMPEG=false
fi

# Cài đặt dependencies nếu chưa có
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate

echo "📦 Installing/updating dependencies..."
pip install -r requirements.txt

# Set environment variables
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
export USE_FFMPEG=$USE_FFMPEG

# Chạy bot với auto-restart
while true; do
    echo "🤖 Starting bot..."
    python3.12 bot_refactored.py
    
    echo "💥 Bot crashed! Restarting in 5 seconds..."
    sleep 5
done
