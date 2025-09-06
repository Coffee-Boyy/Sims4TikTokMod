"""
Configuration settings for TikTok Bridge Service
"""

# TikTok Live Settings
TIKTOK_USERNAME = "your_tiktok_username"  # Replace with your TikTok username

# WebSocket Settings
WEBSOCKET_HOST = "localhost"
WEBSOCKET_PORT = 8765

# Rate Limiting Settings
MIN_EVENT_INTERVAL = 2  # Minimum seconds between events
MAX_EVENTS_PER_MINUTE = 10  # Maximum events per minute

# Logging Settings
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Gift Mapping (for reference - actual mapping happens in Sims 4 mod)
GIFT_MAPPINGS = {
    "rose": "Add §500 to household funds",
    "heart": "Apply Happy buff for 4 hours",
    "gg": "Break random household object"
}
