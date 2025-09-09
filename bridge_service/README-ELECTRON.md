# Sims 4 TikTok Bridge - Electron App

This is the Electron desktop application version of the Sims 4 TikTok Bridge. It provides a modern GUI interface for connecting TikTok Live streams to your Sims 4 mod.

## Features

- **Modern GUI Interface**: Easy-to-use desktop application with a beautiful, responsive UI
- **TikTok Live Integration**: Connect to any live TikTok stream and receive gift events
- **Manual Mode**: Test functionality without needing a live TikTok stream
- **Real-time Logging**: See all events and status updates in real-time
- **Manual Commands**: Send test gifts and trigger sim creation manually
- **Status Monitoring**: View connection status and connected Sims 4 clients
- **Live Stream Checker**: Verify if a TikTok user is currently live before connecting

## Installation

1. Make sure you have Node.js 14+ installed
2. Navigate to the bridge_service directory:
   ```bash
   cd /path/to/Sims4TikTokMod/bridge_service
   ```
3. Install dependencies:
   ```bash
   npm install
   ```

## Usage

### Starting the Application

```bash
npm start
```

This will launch the Electron desktop application.

### Using the Application

1. **Connection Settings**:
   - Enter a TikTok username (without @)
   - Set the WebSocket port (default: 8765)
   - Enable Manual Mode if you want to test without TikTok connection
   - Click "Check Live" to verify the user is streaming
   - Click "Start Bridge" to begin

2. **Manual Commands** (when Manual Mode is enabled):
   - **Spawn Sim**: Trigger sim creation for a test user
   - **Send Gift**: Send test gift events with custom diamond counts

3. **Activity Log**:
   - View real-time events and status updates
   - Auto-scroll keeps the latest messages visible
   - Clear log when needed

## Configuration

The application uses the same `config.json` file as the CLI version:

```json
{
  "tiktokUsername": "default_username",
  "websocketPort": 8765,
  "aiAnalysis": {
    "enabled": true,
    "openaiApiKey": "your_api_key_here",
    "model": "gpt-5-mini"
  },
  "diamondTracking": {
    "threshold": 1,
    "timeout": 3600
  }
}
```

## Building Executables

### For macOS:
```bash
npm run build-mac
```

### For Windows:
```bash
npm run build-win
```

### For Linux:
```bash
npm run build-linux
```

### For all platforms:
```bash
npm run build
```

Built applications will be in the `dist/` directory.

## Development

### Development Mode:
```bash
npm run dev
```

This runs Electron with development tools enabled.

### Original CLI Version:
The original CLI version is still available:
```bash
npm run old:start -- --username your_username
npm run old:dev -- --username your_username --verbose
```

## Features Comparison

| Feature | CLI Version | Electron App |
|---------|-------------|--------------|
| TikTok Live Connection | ✅ | ✅ |
| Manual Mode | ✅ | ✅ |
| Gift Processing | ✅ | ✅ |
| AI Appearance Analysis | ✅ | ✅ |
| Diamond Tracking | ✅ | ✅ |
| WebSocket Server | ✅ | ✅ |
| Real-time Logging | Console | GUI Log Panel |
| Manual Commands | CLI Interface | GUI Buttons |
| Status Monitoring | Console | GUI Status Panel |
| Live Stream Checker | Separate Tool | Built-in Button |
| User Interface | Command Line | Modern Desktop GUI |

## Architecture

The Electron app consists of:

- **Main Process** (`electron-main.js`): Handles app lifecycle and IPC
- **Renderer Process** (`renderer.html/js/css`): The GUI interface
- **Preload Script** (`preload.js`): Secure bridge between main and renderer
- **Bridge Service** (`bridge-service.js`): Core TikTok integration logic
- **Check Live** (`check-live.js`): TikTok live stream verification

## Troubleshooting

1. **App won't start**: Make sure all dependencies are installed with `npm install`
2. **TikTok connection fails**: Use the "Check Live" button to verify the user is streaming
3. **No Sims 4 connection**: Check that your Sims 4 mod is running and connecting to the correct port
4. **Build fails**: Ensure you have the latest versions of electron and electron-builder

## Security Notes

- The app uses Electron's security best practices
- Context isolation is enabled
- Node integration is disabled in the renderer
- All communication uses secure IPC channels

## License

MIT License - Same as the original CLI version.
