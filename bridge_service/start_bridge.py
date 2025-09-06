#!/usr/bin/env python3
"""
Convenience script to start the TikTok Bridge Service
"""

import sys
import os
from config import TIKTOK_USERNAME, WEBSOCKET_PORT

def main():
    """Start the bridge service with config settings"""
    if TIKTOK_USERNAME == "your_tiktok_username":
        print("❌ Error: Please configure your TikTok username in config.py")
        print("   Edit config.py and set TIKTOK_USERNAME to your actual TikTok username")
        sys.exit(1)
    
    print(f"🚀 Starting TikTok Bridge Service...")
    print(f"   TikTok Username: {TIKTOK_USERNAME}")
    print(f"   WebSocket Port: {WEBSOCKET_PORT}")
    print(f"   Press Ctrl+C to stop")
    print("-" * 50)
    
    # Import and run the bridge service
    from tiktok_bridge import TikTokBridgeService
    import asyncio
    
    bridge = TikTokBridgeService(TIKTOK_USERNAME, WEBSOCKET_PORT)
    
    try:
        asyncio.run(bridge.run())
    except KeyboardInterrupt:
        print("\n👋 Bridge service stopped")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
