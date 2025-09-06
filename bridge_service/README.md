# TikTok Bridge Service

This service connects to TikTok Live streams and forwards gift events to the Sims 4 mod via WebSocket.

## Setup

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure TikTok Username**:
   Edit `config.py` and set your TikTok username:
   ```python
   TIKTOK_USERNAME = "your_actual_username"
   ```

## Usage

### Start the Bridge Service

```bash
python tiktok_bridge.py --username your_tiktok_username
```

Or use the config file:
```bash
python tiktok_bridge.py --username $(python -c "from config import TIKTOK_USERNAME; print(TIKTOK_USERNAME)")
```

### Test the Connection

In a separate terminal, run the test client:
```bash
python test_client.py
```

## How It Works

1. **TikTok Live Connection**: Connects to your TikTok Live stream using the TikTokLive library
2. **Event Processing**: Listens for gift events and normalizes them into JSON format
3. **Rate Limiting**: Implements safety measures to prevent spam (max 10 events/minute, 2-second intervals)
4. **WebSocket Broadcasting**: Sends events to all connected Sims 4 mod clients on localhost:8765

## Event Format

Events are sent in the following JSON format:
```json
{
    "user": "viewer_username",
    "gift": "rose",
    "value": 1,
    "timestamp": "2024-01-15T10:30:45"
}
```

## Supported Gifts (MVP)

- **rose** → Add §500 to household funds
- **heart** → Apply Happy buff for 4 hours  
- **gg** → Break random household object

## Troubleshooting

- **Connection Refused**: Make sure the bridge service is running before starting the Sims 4 mod
- **No Events**: Verify you're live on TikTok and receiving gifts
- **Rate Limited**: The service automatically rate-limits events to prevent spam

## Security

- Only accepts connections from localhost
- Implements rate limiting to prevent abuse
- No external network access required for the Sims 4 mod
