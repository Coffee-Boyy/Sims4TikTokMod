# 🎮 Sims 4 TikTok Live Interaction Mod

A revolutionary Sims 4 mod that allows TikTok Live viewers to directly influence your gameplay through gifts and interactions while you stream live to TikTok! Built with modern architecture featuring an Electron-based bridge service and S4CL-powered mod integration.

## 🌟 Features

### 🎁 **Real-Time TikTok Integration**
- Connect your TikTok Live stream directly to Sims 4 gameplay
- Viewers can send gifts that trigger instant in-game actions
- Live interaction between your audience and your Sims
- Support for 40+ different TikTok gift types with configurable actions

### 💫 **Advanced Gift-to-Action System**
- **Rose** → Add 500 simoleons to household funds
- **Heart** → Apply Happy buff for 4 hours to active Sim
- **Diamond** → Add 1000 simoleons to household funds
- **Flirty Compliment** → Apply flirty buff to all household members
- **Lion** → Celebrity spotted event
- **Rocket** → House fire event
- **GG** → Break random household object
- **And many more!** - All gifts are fully configurable through the bridge UI

### 🎨 **Sim Character Creation**
- **AI-Powered Appearance Analysis** - Automatically creates Sims based on TikTok profile pictures
- **Smart Feature Detection** - Analyzes facial features, hair, and style preferences
- **Customizable Creation Rules** - Configure which gifts trigger Sim creation
- **Real-time Preview** - See created Sims instantly in your household

### 🖥️ **Professional Bridge Application**
- **Modern Electron UI** - Beautiful, responsive interface with dark/light theme support
- **Live Configuration** - Modify gift mappings without restarting
- **Real-time Monitoring** - Connection status, client count, and activity logs
- **Gift Testing** - Test any gift action with a single click
- **Auto-reconnection** - Seamless recovery from connection issues

### 🛡️ **Safety & Performance**
- **Rate Limiting** - Prevents spam with configurable thresholds
- **Graceful Error Handling** - User-friendly notifications for all error states
- **Localhost-only Connections** - Secure WebSocket communication
- **Non-blocking Architecture** - Zero impact on game performance
- **Automatic Retry Logic** - Robust connection management

### 📱 **Enhanced In-Game Experience**
- **Clean Notifications** - Streamlined, emoji-free notifications that display properly in Sims 4
- **Connection Status** - Real-time feedback about bridge service connectivity
- **Smart Buffering** - Like accumulation system with threshold-based rewards
- **Household-wide Effects** - Many actions affect all household members

## 🏗️ Architecture

```
TikTok Live Stream → TikTok Live Connector → Bridge Service (Electron) → WebSocket → Sims 4 Mod (S4CL)
```

The system consists of three main components:

### 1. **TikTok Live Connector** (Node.js Library)
- Connects to TikTok Live API using `tiktok-live-connector`
- Processes real-time gift events and viewer interactions
- Handles TikTok's rate limiting and connection management

### 2. **Bridge Service** (Electron Application)
- **Frontend**: Modern web-based UI for configuration and monitoring
- **Backend**: WebSocket server that forwards events to Sims 4
- **Features**: Gift mapping, testing, logging, and connection management
- **AI Integration**: OpenAI-powered Sim creation from profile pictures

### 3. **Sims 4 Mod** (S4CL-based Python)
- **Event Processing**: Receives and processes TikTok events
- **Action Execution**: Maps gifts to in-game effects using S4CL utilities
- **Notification System**: Shows user-friendly in-game notifications
- **Error Handling**: Graceful handling of connection and execution errors

## 🚀 Quick Start

### Prerequisites
- **The Sims 4** with latest updates
- **Sims 4 Community Library (S4CL)** - Latest version
- **Node.js 14+** (for bridge service)
- **TikTok account** with live streaming capability

### Installation

#### 1. Install the Sims 4 Mod
1. Download the latest release from the [Releases page](../../releases)
2. Extract `SimsTikTokMod_sims_tik_tok_mod.ts4script` to your Sims 4 Mods folder:
   ```
   Documents/Electronic Arts/The Sims 4/Mods/
   ```
3. Ensure S4CL is also installed in your Mods folder
4. Enable script mods in Sims 4 settings

#### 2. Set Up the Bridge Service
1. Navigate to the `bridge_service` folder
2. Install dependencies:
   ```bash
   cd bridge_service
   npm install
   ```
3. Start the bridge application:
   ```bash
   npm start
   ```

#### 3. Configure and Connect
1. **Launch the Bridge App** - The Electron interface will open automatically
2. **Enter TikTok Username** - Input your TikTok username (without @)
3. **Start Bridge** - Click the start button to connect to TikTok Live
4. **Launch The Sims 4** - Load a household and you'll see connection notifications
5. **Go Live on TikTok** - Start streaming and receive gifts!

## 📖 Detailed Configuration

### Bridge Service Configuration

The bridge service offers extensive configuration through its modern UI:

#### Gift Mapping Configuration
- **40+ Gift Types**: From basic roses to exclusive luxury items
- **Configurable Actions**: Each gift can trigger different Sims interactions
- **Tier-based Organization**: Basic, Premium, Luxury, and Exclusive gift tiers
- **Real-time Testing**: Test any gift action instantly
- **Persistent Settings**: Configuration automatically saved

#### Available Sims 4 Actions
- **Social Interactions**: Friendly/Romantic hugs, kisses, compliments
- **Mood Effects**: Happy, flirty, and other buff applications
- **Household Effects**: Money addition, object interactions
- **Special Events**: Sim creation, celebrity encounters, emergencies
- **Custom Actions**: Easily extensible for new behaviors

#### AI Sim Creation Settings
- **OpenAI Integration**: Requires API key for profile picture analysis
- **Creation Triggers**: Configure which gifts create new Sims
- **Appearance Analysis**: Automatic feature detection and Sim generation
- **Fallback Options**: Manual creation when AI is unavailable

### Advanced Features

#### Connection Management
- **Auto-reconnection**: Automatic retry with exponential backoff
- **Status Monitoring**: Real-time connection and client status
- **Error Recovery**: Graceful handling of network issues
- **Multiple Clients**: Support for multiple Sims 4 instances

#### Rate Limiting & Safety
```json
{
  "rateLimiting": {
    "likesThreshold": 100,
    "likesTimeout": 60,
    "maxEventsPerMinute": 30
  }
}
```

#### Logging & Debugging
- **Activity Logs**: Real-time event tracking with timestamps
- **Error Reporting**: Detailed error information with stack traces
- **Debug Mode**: Verbose logging for troubleshooting
- **Export Logs**: Save logs for analysis

## 🛠️ Development & Customization

### Project Structure
```
├── bridge_service/          # Electron bridge application
│   ├── electron-main.js     # Main Electron process
│   ├── renderer.html        # UI interface
│   ├── renderer.js          # Frontend logic
│   ├── bridge-service.js    # TikTok connection logic
│   └── package.json         # Dependencies and scripts
├── Scripts/                 # Sims 4 mod source code
│   └── sims_tik_tok_mod/    # Main mod package
│       ├── modinfo.py       # Mod information
│       ├── tiktok_bridge_client.py    # WebSocket client
│       ├── notifications/   # Notification system
│       └── sim_character_creator.py  # AI Sim creation
├── Libraries/               # S4CL dependency
└── Release/                 # Compiled mod files
```

### Adding New Gift Actions

1. **Define the Action** in `tiktok_gift_notifications.py`:
```python
ACTION_DESCRIPTIONS = {
    'new_gift': 'Custom action description!',
    # ... other actions
}
```

2. **Implement the Effect** in `_apply_action_effect()`:
```python
elif action == 'new_gift':
    # Your custom logic here
    log.info("Custom action executed!")
```

3. **Configure in Bridge UI** - Map the gift to your new action

### Extending the Bridge Service

The bridge service is built with modern web technologies and can be easily extended:

- **Frontend**: HTML/CSS/JavaScript with responsive design
- **Backend**: Node.js with WebSocket support
- **Packaging**: Electron for cross-platform distribution
- **APIs**: RESTful endpoints for configuration management

## 🛠️ Troubleshooting

### Common Issues

#### Connection Problems
- **"Cannot connect to TikTok bridge service"**
  - Ensure bridge service is running (`npm start`)
  - Check that port 8765 is not blocked by firewall
  - Verify TikTok username is correct

#### Sims 4 Integration Issues
- **Mod not loading**
  - Verify S4CL is installed and up to date
  - Enable script mods in game settings
  - Check mod files are in correct Mods folder

#### TikTok Live Connection
- **Not receiving gifts**
  - Confirm you're live on TikTok
  - Check username spelling in bridge service
  - Verify TikTok Live permissions

### Debug Mode
Enable detailed logging in the bridge service:
```bash
npm run dev  # Development mode with verbose logging
```

Check Sims 4 mod logs:
```
Documents/Electronic Arts/The Sims 4/mod_logs/SimsTikTokMod_1.0_Messages.txt
```

### Performance Optimization
- **Rate Limiting**: Adjust thresholds in bridge configuration
- **Gift Filtering**: Disable unused gift types to reduce processing
- **Connection Pooling**: Bridge service handles multiple connections efficiently

## 🔮 Roadmap & Future Enhancements

### Short Term
- [ ] **Mobile Companion App** - Control bridge service from phone
- [ ] **Streamer Dashboard** - Enhanced analytics and viewer engagement metrics
- [ ] **Custom Sound Effects** - Audio feedback for gift actions
- [ ] **Viewer Leaderboards** - Track top contributors

### Long Term
- [ ] **Multi-Platform Support** - YouTube Live, Twitch integration
- [ ] **Advanced AI Features** - Personality-based Sim creation
- [ ] **Community Marketplace** - Share custom gift action configurations
- [ ] **VR Integration** - Mixed reality streaming experiences

### Technical Improvements
- [ ] **Database Integration** - Persistent viewer and event tracking
- [ ] **Cloud Sync** - Configuration backup and sync across devices
- [ ] **Plugin Architecture** - Third-party action development
- [ ] **Performance Metrics** - Real-time performance monitoring

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup
1. Clone the repository
2. Install bridge service dependencies: `cd bridge_service && npm install`
3. Set up Sims 4 development environment with S4CL
4. Configure development TikTok account for testing

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Sims 4 Community Library (S4CL)** - The powerful foundation that makes this mod possible
- **TikTok Live Connector** - Excellent Node.js library for TikTok Live API integration
- **Electron** - Cross-platform desktop application framework
- **OpenAI** - AI-powered Sim creation capabilities
- **The Sims 4 Modding Community** - Inspiration, feedback, and continuous support

---

**Built with ❤️ by CoffeeBoy**

*Transform your Sims 4 streams into interactive experiences that your viewers will never forget!*