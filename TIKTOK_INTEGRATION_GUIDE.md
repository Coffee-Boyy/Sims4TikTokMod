# 🎮 Sims 4 TikTok Integration Guide

This guide explains how to use the complete TikTok Live integration with your Sims 4 mod, allowing TikTok gifts to trigger in-game notifications and effects.

## 🏗️ System Architecture

```
TikTok Live Stream → Node.js Bridge → WebSocket → Sims 4 Mod → In-Game Notifications
```

1. **Node.js Bridge** connects to TikTok Live and captures gift events
2. **WebSocket Server** in the bridge forwards events to the Sims mod
3. **Sims 4 Mod** receives events and displays notifications in-game

## 📋 Prerequisites

- **The Sims 4** with mods enabled
- **Node.js** 14.0.0 or higher (for the bridge)
- **Python 3.7+** (for Sims 4 scripting)
- **S4CL (Sims 4 Community Library)** installed in your Sims 4 mods folder

## 🚀 Setup Instructions

### Step 1: Install Node.js Bridge Dependencies

```bash
cd bridge_service
npm install
```

### Step 2: Install Python WebSocket Client

Navigate to the Scripts folder and run the dependency installer:

```bash
cd Scripts
python install_dependencies.py
```

Or install manually:
```bash
pip install websocket-client
```

### Step 3: Configure the Bridge

Edit `bridge_service/config.json`:
```json
{
  "tiktokUsername": "your_tiktok_streamer_username",
  "websocketPort": 8765
}
```

### Step 4: Install the Sims 4 Mod

1. Copy the entire `Scripts/sims_tik_tok_mod` folder to your Sims 4 Mods folder
2. Make sure S4CL is also installed in your Mods folder
3. Enable script mods in The Sims 4 settings

## 🎯 How to Use

### 1. Start the Bridge Service

```bash
cd bridge_service
node start.js --username your_streamer_name --verbose
```

You should see:
```
✅ Connected to TikTok Live! Room ID: 1234567890
✅ WebSocket server listening on localhost:8765
```

### 2. Start The Sims 4

1. Launch The Sims 4
2. Load a household
3. Look for the mod loaded notification: "🎮 Sims 4 TikTok Mod - Mod loaded! Connecting to TikTok bridge..."

### 3. Test the Integration

When someone sends a gift on the TikTok stream, you should see:

**In the bridge console:**
```
🎁 Processing gift: username sent "Popular Vote" (x1) [1 💎]
📤 Sent to client: {"type":"gift","user":"username"...}
```

**In The Sims 4:**
A notification popup saying:
```
🎁 TikTok Gift Received!
username sent Popular Vote!
🗳️ Popularity boost!
💎 Worth 1 diamonds
```

## 🎁 Gift Mappings

The mod includes predefined actions for common gifts:

| Gift Name | In-Game Effect |
|-----------|----------------|
| Rose | 💐 Added §500 to household funds! |
| Popular Vote | 🗳️ Popularity boost! |
| Heart | ❤️ Applied Happy buff for 4 hours! |
| GG | 💥 Something broke in the house! |
| Diamond | 💎 Added §1000 to household funds! |
| Rocket | 🚀 House is on fire! |
| Lion | 🦁 Celebrity spotted! |
| *Other* | 🎁 Thank you for the gift! |

## 🔧 Customization

### Adding New Gift Effects

Edit `Scripts/sims_tik_tok_mod/notifications/tiktok_gift_notifications.py`:

```python
GIFT_ACTIONS = {
    'rose': '💐 Added §500 to household funds!',
    'your_custom_gift': '🎉 Your custom effect!',
    # Add more gifts here
}
```

### Implementing Actual Game Effects

In the same file, modify the `_apply_gift_effect` method:

```python
@staticmethod
def _apply_gift_effect(gift_key: str, count: int) -> None:
    if gift_key == 'rose':
        # Add money to active household
        from sims4communitylib.utils.sims.common_household_utils import CommonHouseholdUtils
        active_household = CommonHouseholdUtils.get_active_household()
        if active_household:
            active_household.funds.add(500 * count)
    
    elif gift_key == 'heart':
        # Apply happy buff to active sim
        from sims4communitylib.utils.sims.common_sim_utils import CommonSimUtils
        active_sim = CommonSimUtils.get_active_sim()
        if active_sim:
            # Add your buff logic here
            pass
```

## 🐛 Troubleshooting

### Bridge Connection Issues

**Problem:** "Failed to connect to TikTok Live"
- **Solution:** Make sure the TikTok user is actively live streaming
- **Check:** Try `node check-live.js username` to verify

**Problem:** "WebSocket connection failed"
- **Solution:** Check if port 8765 is available
- **Try:** Use a different port with `--port 9000`

### Sims 4 Mod Issues

**Problem:** "WebSocket client not available"
- **Solution:** Install websocket-client: `pip install websocket-client`

**Problem:** No notifications appearing in-game
- **Check:** Make sure script mods are enabled in Sims 4 settings
- **Check:** Look for mod errors in the game's log files
- **Check:** Verify S4CL is properly installed

**Problem:** "TikTok bridge WebSocket error"
- **Solution:** Make sure the bridge service is running before starting Sims 4
- **Try:** Restart both the bridge and Sims 4

### Debug Mode

Enable detailed logging in the bridge:
```bash
node start.js --username streamer --verbose --debug
```

Check Sims 4 mod logs in:
- Windows: `Documents/Electronic Arts/The Sims 4/mod_logs/`
- Mac: `Documents/Electronic Arts/The Sims 4/mod_logs/`

## 🔄 Development Workflow

1. **Start Bridge:** `node start.js --username streamer --verbose`
2. **Start Sims 4:** Load household and check for connection notification
3. **Test Gifts:** Have someone send gifts on the TikTok stream
4. **Monitor Logs:** Watch both bridge console and Sims 4 for any issues
5. **Iterate:** Modify gift effects and restart as needed

## 📁 File Structure

```
Scripts/sims_tik_tok_mod/
├── __init__.py
├── modinfo.py
├── tiktok_bridge_client.py          # WebSocket client
├── enums/
│   └── string_enums.py
└── notifications/
    ├── show_loaded_notification.py   # Mod initialization
    └── tiktok_gift_notifications.py  # Gift handling
```

## 🤝 Contributing

Feel free to:
- Add new gift effects
- Improve the WebSocket connection reliability
- Add more TikTok event types (follows, likes, etc.)
- Create better in-game visual effects

## 📄 License

This integration is provided as-is for educational and entertainment purposes. Make sure to comply with TikTok's Terms of Service when using their Live API.
