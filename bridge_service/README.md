# 🎮 Sims 4 TikTok Bridge Service (Node.js)

A Node.js bridge service that connects to TikTok Live streams and forwards gift events to your Sims 4 mod via WebSocket.

## ✨ Features

- 🎁 **Real-time Gift Detection** - Captures TikTok gifts and forwards them to your Sims 4 mod
- 🌐 **WebSocket Server** - Provides real-time communication with your Sims 4 mod
- ⏱️ **Rate Limiting** - Prevents spam and ensures smooth gameplay
- 🔍 **Verbose Logging** - Optional detailed logging for debugging
- 🛡️ **Error Handling** - Comprehensive error handling with helpful debugging tips
- ⚙️ **Configurable** - Easy configuration via JSON file or command line

## 📋 Requirements

- **Node.js** 14.0.0 or higher
- **npm** (comes with Node.js)
- **Internet connection**
- **TikTok user must be actively live streaming**

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd bridge_service
npm install
```

### 2. Configure Username

Edit `config.json` and set your desired TikTok username:

```json
{
  "tiktokUsername": "your_tiktok_username_here"
}
```

### 3. Start the Bridge

```bash
npm start
```

Or with custom username:

```bash
node start.js --username shirleycoelloc
```

### 4. Test the Connection

In another terminal:

```bash
npm test
```

This will start a test client that simulates your Sims 4 mod connecting to the bridge.

## 📖 Usage

### Basic Usage

```bash
# Use username from config.json
node start.js

# Specify username
node start.js --username popular_streamer

# Custom port and verbose logging
node start.js --username streamer --port 9000 --verbose
```

### Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--username` | TikTok username (without @) | From config.json |
| `--port` | WebSocket port | 8765 |
| `--verbose` | Enable detailed logging | false |
| `--help` | Show help message | - |

### Configuration File

Edit `config.json` to customize settings:

```json
{
  "tiktokUsername": "shirleycoelloc",
  "websocketPort": 8765,
  "websocketHost": "localhost",
  "rateLimiting": {
    "minEventInterval": 2000,
    "maxEventsPerMinute": 10
  },
  "logging": {
    "verbose": false
  },
  "giftMappings": {
    "rose": "Add §500 to household funds",
    "heart": "Apply Happy buff for 4 hours",
    "gg": "Break random household object"
  }
}
```

## 📡 WebSocket API

The bridge sends JSON messages to connected clients (your Sims 4 mod):

### Connection Event
```json
{
  "type": "connection",
  "message": "Connected to TikTok Live bridge for @username",
  "timestamp": "2024-01-01T12:00:00.000Z"
}
```

### Gift Event
```json
{
  "type": "gift",
  "user": "tiktok_username",
  "gift": "rose",
  "value": 5,
  "giftId": 5655,
  "diamondCount": 1,
  "timestamp": "2024-01-01T12:00:00.000Z"
}
```

## 🧪 Testing

### Test the Bridge Service

1. **Start the bridge:**
   ```bash
   node start.js --username some_live_user --verbose
   ```

2. **In another terminal, start the test client:**
   ```bash
   node test-client.js
   ```

3. **The test client will:**
   - Connect to the bridge WebSocket server
   - Display any gift events received
   - Show what Sims 4 actions would be triggered

### Manual WebSocket Testing

You can also test with any WebSocket client:

```bash
# Using wscat (install with: npm install -g wscat)
wscat -c ws://localhost:8765
```

## 🔧 Troubleshooting

### Common Issues

**❌ "Failed to connect to TikTok Live"**
- The TikTok user is not currently live streaming
- The username doesn't exist
- Network connectivity issues

**❌ "WebSocket connection failed"**
- Port 8765 is already in use
- Firewall blocking the connection
- Try a different port with `--port 9000`

**❌ "No gift events received"**
- The streamer is not receiving gifts
- Rate limiting is active (wait a moment)
- Enable `--verbose` to see all activity

### Debug Mode

Enable verbose logging to see detailed information:

```bash
node start.js --username streamer --verbose
```

This will show:
- All TikTok events (chat, likes, follows)
- WebSocket connection details
- Rate limiting information
- Detailed error messages

### Finding Live Users

The bridge only works with users who are **actively live streaming**. To find live users:

1. Open TikTok in your web browser
2. Search for "LIVE" content
3. Find a user who is currently streaming
4. Use their username (without the @) in the bridge

## 📁 Project Structure

```
bridge_service/
├── package.json          # Dependencies and scripts
├── config.json          # Configuration settings
├── bridge.js            # Main bridge service
├── start.js             # Startup script with nice interface
├── test-client.js       # Test client for debugging
└── README.md           # This file
```

## 🔌 Integration with Sims 4

Your Sims 4 mod should:

1. **Connect** to `ws://localhost:8765`
2. **Listen** for messages with `type: "gift"`
3. **Process** the gift data to trigger in-game actions
4. **Optionally** send responses back to the bridge

Example WebSocket connection in your mod:
```javascript
// Pseudocode for Sims 4 mod
const ws = new WebSocket('ws://localhost:8765');

ws.on('message', (data) => {
    const event = JSON.parse(data);
    if (event.type === 'gift') {
        triggerSimsAction(event.gift, event.user, event.value);
    }
});
```

## 🤝 Contributing

Feel free to submit issues, feature requests, or pull requests!

## 📄 License

MIT License - feel free to use this in your projects!

## 🙏 Acknowledgments

- [TikTok-Live-Connector](https://github.com/zerodytrash/TikTok-Live-Connector) - The awesome library that makes this possible
- The Sims 4 modding community
- TikTok Live streamers who make this fun!
