#!/bin/bash
# Installation script for TikTok Bridge Service

echo "🔧 Installing TikTok Bridge Service dependencies..."

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed"
    exit 1
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is required but not installed"
    exit 1
fi

# Install requirements
echo "📦 Installing Python packages..."
pip3 install -r requirements.txt

if [ $? -eq 0 ]; then
    echo "✅ Installation completed successfully!"
    echo ""
    echo "Next steps:"
    echo "1. Edit config.py and set your TikTok username"
    echo "2. Run: python3 start_bridge.py"
    echo "3. In another terminal, run: python3 test_client.py"
else
    echo "❌ Installation failed"
    exit 1
fi
