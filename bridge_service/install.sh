#!/bin/bash
# Installation script for TikTok Bridge Service (Node.js)

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║              🎮 SIMS 4 TIKTOK BRIDGE INSTALLER 🎮            ║"
echo "║                       Node.js Edition                        ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed!"
    echo "Please install Node.js 14.0.0 or higher from https://nodejs.org/"
    exit 1
fi

# Check Node.js version
NODE_VERSION=$(node -v | cut -d'v' -f2)
REQUIRED_VERSION="14.0.0"

if ! printf '%s\n%s\n' "$REQUIRED_VERSION" "$NODE_VERSION" | sort -V -C; then
    echo "❌ Node.js version $NODE_VERSION is too old!"
    echo "Please install Node.js $REQUIRED_VERSION or higher"
    exit 1
fi

echo "✅ Node.js $NODE_VERSION detected"

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "❌ npm is not installed!"
    echo "Please install npm (usually comes with Node.js)"
    exit 1
fi

echo "✅ npm detected"

# Install dependencies
echo "📦 Installing dependencies..."
npm install

if [ $? -eq 0 ]; then
    echo "✅ Dependencies installed successfully!"
else
    echo "❌ Failed to install dependencies"
    exit 1
fi

# Make scripts executable
chmod +x start.js
chmod +x test-client.js
chmod +x bridge.js

echo ""
echo "🎉 Installation complete!"
echo ""
echo "📋 Next steps:"
echo "   1. Edit config.json and set your TikTok username"
echo "   2. Run: npm start"
echo "   3. Or: node start.js --username your_tiktok_user"
echo ""
echo "🧪 To test:"
echo "   1. Start bridge: npm start"
echo "   2. In another terminal: npm test"
echo ""
echo "📖 For more info, see README.md"
echo ""
echo "⚠️  Remember: The TikTok user must be actively live streaming!"
