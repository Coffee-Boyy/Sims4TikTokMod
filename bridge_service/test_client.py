#!/usr/bin/env python3
"""
Test client for TikTok Bridge Service
Connects to the WebSocket server and displays received events
"""

import asyncio
import json
import websockets
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_client():
    """Test client that connects to the bridge service"""
    uri = "ws://localhost:8765"
    
    try:
        logger.info(f"Connecting to {uri}...")
        async with websockets.connect(uri) as websocket:
            logger.info("Connected to TikTok Bridge Service!")
            logger.info("Waiting for TikTok gift events...")
            logger.info("(Start the bridge service and go live on TikTok to see events)")
            
            async for message in websocket:
                try:
                    event = json.loads(message)
                    logger.info(f"Received event: {event}")
                    
                    # Pretty print the event
                    print(f"\n🎁 TikTok Gift Event:")
                    print(f"   User: {event['user']}")
                    print(f"   Gift: {event['gift']}")
                    print(f"   Value: {event['value']}")
                    print(f"   Time: {event['timestamp']}")
                    print("-" * 40)
                    
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse message: {e}")
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    
    except websockets.exceptions.ConnectionRefused:
        logger.error("Connection refused. Make sure the bridge service is running.")
    except Exception as e:
        logger.error(f"Connection error: {e}")

if __name__ == "__main__":
    asyncio.run(test_client())
