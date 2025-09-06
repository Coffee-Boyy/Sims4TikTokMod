# 🎮 Sims 4 TikTok Live Interaction Mod

A revolutionary Sims 4 mod that allows TikTok Live viewers to directly influence your gameplay through gifts and interactions while you stream live to TikTok!

## 🌟 Features

### 🎁 **Real-Time TikTok Integration**
- Connect your TikTok Live stream to Sims 4 gameplay
- Viewers can send gifts that trigger in-game actions
- Live interaction between your audience and your Sims

### 💰 **Gift-to-Action System**
- **🌹 Rose** → Add §500 to household funds
- **❤️ Heart** → Apply "Happy" buff for 4 hours to active Sim
- **🎮 GG** → Break one random household object (chaos mode!)

### 🛡️ **Safety & Performance**
- Rate limiting prevents spam (max 10 events/minute)
- Localhost-only connections for security
- Non-blocking architecture won't affect game performance
- Graceful error handling and reconnection

### 📱 **Live Notifications**
- Real-time popup notifications for every TikTok event
- Clear feedback showing viewer actions and effects
- Beautiful in-game UI integration

## 🏗️ Architecture

```
TikTok Live Stream → Bridge Service → WebSocket → Sims 4 Mod
```

The system consists of two main components:

1. **Bridge Service** (External Python process)
   - Connects to TikTok Live API
   - Processes gift events
   - Forwards events to Sims 4 mod via WebSocket

2. **Sims 4 Mod** (S4CL-based)
   - Listens for events from bridge service
   - Maps gifts to in-game actions
   - Executes effects and shows notifications

## 🚀 Quick Start

### Prerequisites
- **The Sims 4** with latest updates
- **Sims 4 Community Library (S4CL)** mod
- **Python 3.7+** (for bridge service)
- **TikTok account** with live streaming capability

### Installation

#### 1. Install the Sims 4 Mod
1. Download the latest release from the [Releases page](../../releases)
2. Extract `SimsTikTokMod.ts4script` to your Sims 4 Mods folder:
   ```
   Documents/Electronic Arts/The Sims 4/Mods/
   ```
3. Ensure S4CL is also installed in your Mods folder

#### 2. Set Up the Bridge Service
1. Navigate to the `bridge_service` folder
2. Install dependencies:
   ```bash
   cd bridge_service
   ./install.sh
   ```
3. Configure your TikTok username in `config.py`:
   ```python
   TIKTOK_USERNAME = "your_actual_tiktok_username"
   ```

#### 3. Start Streaming!
1. **Start the bridge service:**
   ```bash
   python3 start_bridge.py
   ```
2. **Launch The Sims 4** and load a household
3. **Go live on TikTok** and start receiving gifts!

## 📖 Detailed Setup Guide

### Bridge Service Configuration

The bridge service runs independently and connects your TikTok Live stream to the Sims 4 mod.

#### Configuration Options (`config.py`)
```python
# TikTok Settings
TIKTOK_USERNAME = "your_tiktok_username"

# WebSocket Settings  
WEBSOCKET_HOST = "localhost"
WEBSOCKET_PORT = 8765

# Rate Limiting
MIN_EVENT_INTERVAL = 2  # seconds between events
MAX_EVENTS_PER_MINUTE = 10
```

#### Testing the Connection
Before going live, test your setup:
```bash
# Terminal 1: Start bridge service
python3 start_bridge.py

# Terminal 2: Run test client
python3 test_client.py
```

### Sims 4 Mod Features

#### Event Processing
The mod automatically:
- Connects to the bridge service on game load
- Processes incoming TikTok gift events
- Maps gifts to appropriate in-game actions
- Shows notifications for all events

#### Supported Actions
| Gift | Effect | Description |
|------|--------|-------------|
| 🌹 Rose | +§500 Funds | Adds money to household |
| ❤️ Heart | Happy Buff | 4-hour happiness boost |
| 🎮 GG | Break Object | Random object destruction |

## 🛠️ Troubleshooting

### Debug Mode
Enable verbose logging in the bridge service:
```bash
python3 tiktok_bridge.py --username your_username --verbose
```

## 🔮 Future Enhancements

- **Configurable Actions**: JSON-based gift-to-action mapping
- **Viewer Statistics**: Track viewer engagement and favorites
- **Angel/Gremlin System**: Dual-meter viewer influence system
- **AI Narrator**: Text-to-speech reactions to events
- **Multi-Household Support**: Support for multiple save files
- **Custom UI Panel**: In-game control panel for streamers

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Sims 4 Community Library** - The foundation that makes this mod possible
- **TikTokLive Python Library** - For TikTok Live API integration
- **The Sims 4 Community** - For inspiration and feedback
