#!/usr/bin/env python3
"""
TikTok Live Bridge Service for Sims 4 Mod
Connects to TikTok Live stream and forwards gift events to Sims 4 mod via WebSocket
"""

import asyncio
import json
import logging
import time
from typing import Set, Dict, Any
import websockets
from TikTokLive import TikTokLiveClient
from TikTokLive.events import GiftEvent, ConnectEvent, DisconnectEvent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TikTokBridgeService:
    """Bridge service that connects TikTok Live to Sims 4 mod via WebSocket"""
    
    def __init__(self, tiktok_username: str, websocket_port: int = 8765):
        self.tiktok_username = tiktok_username
        self.websocket_port = websocket_port
        self.connected_clients: Set[websockets.WebSocketServerProtocol] = set()
        self.last_sent_time = 0
        self.min_interval = 2  # Minimum 2 seconds between events
        self.max_events_per_minute = 10
        self.events_this_minute = 0
        self.minute_start_time = time.time()
        
        # Initialize TikTok client
        self.tiktok_client = TikTokLiveClient(unique_id=tiktok_username)
        self._setup_tiktok_events()
    
    def _setup_tiktok_events(self):
        """Set up TikTok Live event handlers"""
        
        @self.tiktok_client.on(ConnectEvent)
        async def on_connect(event: ConnectEvent):
            logger.info(f"Connected to TikTok Live stream: {self.tiktok_username}")
        
        @self.tiktok_client.on(DisconnectEvent)
        async def on_disconnect(event: DisconnectEvent):
            logger.warning(f"Disconnected from TikTok Live stream: {self.tiktok_username}")
        
        @self.tiktok_client.on(GiftEvent)
        async def on_gift(event: GiftEvent):
            """Handle TikTok gift events"""
            await self._process_gift_event(event)
    
    async def _process_gift_event(self, event: GiftEvent):
        """Process and forward gift events with rate limiting"""
        current_time = time.time()
        
        # Reset minute counter if needed
        if current_time - self.minute_start_time >= 60:
            self.events_this_minute = 0
            self.minute_start_time = current_time
        
        # Check rate limits
        if (current_time - self.last_sent_time < self.min_interval or 
            self.events_this_minute >= self.max_events_per_minute):
            logger.info(f"Rate limited: Skipping gift from {event.user.nickname}")
            return
        
        # Update rate limiting counters
        self.last_sent_time = current_time
        self.events_this_minute += 1
        
        # Create event payload according to requirements
        payload = {
            "user": event.user.nickname,
            "gift": event.gift.name.lower(),  # Normalize gift name
            "value": event.gift.count if hasattr(event.gift, 'count') else 1,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())
        }
        
        logger.info(f"Processing gift: {payload['user']} sent {payload['gift']} (x{payload['value']})")
        
        # Send to all connected Sims 4 mod clients
        await self._broadcast_to_clients(payload)
    
    async def _broadcast_to_clients(self, payload: Dict[str, Any]):
        """Broadcast event to all connected WebSocket clients"""
        if not self.connected_clients:
            logger.warning("No Sims 4 mod clients connected")
            return
        
        message = json.dumps(payload)
        disconnected_clients = set()
        
        for client in self.connected_clients:
            try:
                await client.send(message)
                logger.debug(f"Sent to client: {message}")
            except websockets.exceptions.ConnectionClosed:
                disconnected_clients.add(client)
            except Exception as e:
                logger.error(f"Error sending to client: {e}")
                disconnected_clients.add(client)
        
        # Remove disconnected clients
        self.connected_clients -= disconnected_clients
    
    async def websocket_handler(self, websocket, path):
        """Handle WebSocket connections from Sims 4 mod"""
        client_info = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
        logger.info(f"Sims 4 mod connected: {client_info}")
        
        self.connected_clients.add(websocket)
        
        try:
            # Keep connection alive and handle any incoming messages
            async for message in websocket:
                logger.debug(f"Received from {client_info}: {message}")
                # Could handle mod responses here if needed
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Sims 4 mod disconnected: {client_info}")
        except Exception as e:
            logger.error(f"Error handling client {client_info}: {e}")
        finally:
            self.connected_clients.discard(websocket)
    
    async def start_websocket_server(self):
        """Start the WebSocket server"""
        logger.info(f"Starting WebSocket server on localhost:{self.websocket_port}")
        
        async with websockets.serve(
            self.websocket_handler, 
            "localhost", 
            self.websocket_port
        ):
            logger.info("WebSocket server started successfully")
            await asyncio.Future()  # Run forever
    
    async def start_tiktok_client(self):
        """Start the TikTok Live client"""
        logger.info(f"Starting TikTok Live client for: {self.tiktok_username}")
        await self.tiktok_client.run()
    
    async def run(self):
        """Run both the WebSocket server and TikTok client concurrently"""
        logger.info("Starting TikTok Bridge Service...")
        
        # Create tasks for both services
        websocket_task = asyncio.create_task(self.start_websocket_server())
        tiktok_task = asyncio.create_task(self.start_tiktok_client())
        
        try:
            # Run both services concurrently
            await asyncio.gather(websocket_task, tiktok_task)
        except KeyboardInterrupt:
            logger.info("Shutting down bridge service...")
        except Exception as e:
            logger.error(f"Error in bridge service: {e}")
        finally:
            # Cleanup
            websocket_task.cancel()
            tiktok_task.cancel()

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="TikTok Live Bridge Service for Sims 4 Mod")
    parser.add_argument(
        "--username", 
        required=True, 
        help="TikTok username to connect to (without @)"
    )
    parser.add_argument(
        "--port", 
        type=int, 
        default=8765, 
        help="WebSocket port (default: 8765)"
    )
    parser.add_argument(
        "--verbose", 
        action="store_true", 
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create and run bridge service
    bridge = TikTokBridgeService(args.username, args.port)
    
    try:
        asyncio.run(bridge.run())
    except KeyboardInterrupt:
        logger.info("Bridge service stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")

if __name__ == "__main__":
    main()
