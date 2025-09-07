"""
TikTok Bridge WebSocket Client for Sims 4 Mod
Connects to the Node.js bridge service and handles gift events
"""
import json
import threading
import time
from typing import Optional, Callable, Dict, Any

try:
    # Try to import websocket-client (already present in Scripts folder)
    import websocket
    WEBSOCKET_AVAILABLE = True
except ImportError:
    WEBSOCKET_AVAILABLE = False

from sims4communitylib.utils.common_log_registry import CommonLogRegistry
from sims_tik_tok_mod.modinfo import ModInfo

# Create a logger for this module
log = CommonLogRegistry.get().register_log(ModInfo.get_identity(), 'TikTokBridge')
log.enable()

class TikTokBridgeClient:
    """WebSocket client to connect to the TikTok bridge service"""
    
    def __init__(self, host: str = "127.0.0.1", port: int = 8765):
        self.host = host
        self.port = port
        self.url = f"ws://{host}:{port}"
        self.ws: Optional[websocket.WebSocketApp] = None
        self.is_connected = False
        self.is_running = False
        self.connection_thread: Optional[threading.Thread] = None
        
        # Callback for when gift events are received
        self.on_gift_callback: Optional[Callable[[Dict[str, Any]], None]] = None
        
        # Callback for when like events are received
        self.on_like_callback: Optional[Callable[[Dict[str, Any]], None]] = None
        
        # Connection retry settings
        self.max_retries = 5
        self.retry_delay = 5  # seconds
        self.max_retry_delay = 60  # maximum 60 seconds between retries
        self.current_retries = 0
        self.last_retry_time = 0  # timestamp of last retry attempt
        
    def set_gift_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Set the callback function to be called when gift events are received"""
        self.on_gift_callback = callback
        
    def set_like_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Set the callback function to be called when like events are received"""
        self.on_like_callback = callback
        
    def start(self) -> bool:
        """Start the WebSocket client connection"""
        if not WEBSOCKET_AVAILABLE:
            log.error("[TikTokBridge] WebSocket client not available. Please install websocket-client package.")
            return False
            
        if self.is_running:
            log.info("[TikTokBridge] TikTok bridge client is already running")
            return True
            
        log.info("[TikTokBridge] Starting TikTok bridge client...")
        log.info(f"[TikTokBridge] Will attempt to connect to {self.url}")
        log.info("[TikTokBridge] Make sure the bridge service is running with: cd bridge_service && node start.js")
        
        self.is_running = True
        self.current_retries = 0
        
        # Start connection in a separate thread
        self.connection_thread = threading.Thread(target=self._run_connection, daemon=True)
        self.connection_thread.start()
        
        return True
        
    def stop(self) -> None:
        """Stop the WebSocket client"""
        log.info("[TikTokBridge] Stopping TikTok bridge client...")
        self.is_running = False
        
        if self.ws:
            self.ws.close()
            
        if self.connection_thread and self.connection_thread.is_alive():
            self.connection_thread.join(timeout=5)
            
    def _run_connection(self) -> None:
        """Run the WebSocket connection with automatic reconnection"""
        while self.is_running and self.current_retries < self.max_retries:
            try:
                # Check if enough time has passed since last retry (minimum 1 minute)
                current_time = time.time()
                time_since_last_retry = current_time - self.last_retry_time
                
                if self.current_retries > 0 and time_since_last_retry < self.max_retry_delay:
                    # Wait for the remaining time to reach 1 minute
                    wait_time = self.max_retry_delay - time_since_last_retry
                    if self.is_running:
                        time.sleep(wait_time)
                    continue
                
                # Only log connection attempts for first try or after significant delays
                if self.current_retries == 0 or time_since_last_retry >= self.max_retry_delay:
                    log.info(f"[TikTokBridge] Attempting to connect to {self.url}")
                
                self.last_retry_time = current_time
                
                # Create WebSocket connection
                self.ws = websocket.WebSocketApp(
                    self.url,
                    on_open=self._on_open,
                    on_message=self._on_message,
                    on_error=self._on_error,
                    on_close=self._on_close
                )
                
                # Start the connection (this will block until connection is closed)
                self.ws.run_forever()
                
                # If we get here, connection was closed
                if self.is_running:
                    self.current_retries += 1
                    if self.current_retries < self.max_retries:
                        # Use exponential backoff with max delay of 60 seconds
                        delay = min(self.retry_delay * (2 ** (self.current_retries - 1)), self.max_retry_delay)
                        log.info(f"[TikTokBridge] Connection lost. Will retry in {delay} seconds... ({self.current_retries}/{self.max_retries})")
                        time.sleep(delay)
                    else:
                        log.info("[TikTokBridge] Max retries reached. Stopping TikTok bridge client.")
                        break
                        
            except Exception as e:
                # Silent error handling - only log on first attempt or after significant delays
                current_time = time.time()
                time_since_last_retry = current_time - self.last_retry_time
                
                if self.current_retries == 0 or time_since_last_retry >= self.max_retry_delay:
                    log.error(f"[TikTokBridge] Connection error: {e}")
                
                self.current_retries += 1
                if self.is_running and self.current_retries < self.max_retries:
                    # Use exponential backoff with max delay of 60 seconds
                    delay = min(self.retry_delay * (2 ** (self.current_retries - 1)), self.max_retry_delay)
                    time.sleep(delay)
                    
        self.is_running = False
        self.is_connected = False
        
    def _on_open(self, ws) -> None:
        """Called when WebSocket connection is opened"""
        log.info("[TikTokBridge] ✅ Connected to TikTok bridge!")
        self.is_connected = True
        self.current_retries = 0  # Reset retry counter on successful connection
        
    def _on_message(self, ws, message: str) -> None:
        """Called when a message is received from the bridge"""
        try:
            data = json.loads(message)
            event_type = data.get('type', 'unknown')
            
            log.debug(f"Received event: {event_type}")
            
            if event_type == 'gift' and self.on_gift_callback:
                # Call the gift callback
                self.on_gift_callback(data)
            elif event_type == 'like' and self.on_like_callback:
                # Call the like callback
                self.on_like_callback(data)
            elif event_type == 'connection':
                log.info(f"Bridge connection message: {data.get('message', '')}")
                
        except json.JSONDecodeError as e:
            log.error(f"Failed to parse message from bridge: {e}")
        except Exception as e:
            log.error(f"Error handling bridge message: {e}")
            
    def _on_error(self, ws, error) -> None:
        """Called when a WebSocket error occurs"""
        try:
            # Silent error handling - only log errors that are significant
            # Avoid logging common connection errors that happen during reconnection
            current_time = time.time()
            time_since_last_retry = current_time - self.last_retry_time
            
            # Only log errors on first attempt or after significant delays to avoid spam
            if self.current_retries == 0 or time_since_last_retry >= self.max_retry_delay:
                log.error(f"[TikTokBridge] WebSocket error: {error}")
        except:
            # If even logging fails, just pass to avoid crashes
            pass
        
    def _on_close(self, ws, close_status_code, close_msg) -> None:
        """Called when WebSocket connection is closed"""
        # Silent handling for frequent disconnections during reconnection attempts
        current_time = time.time()
        time_since_last_retry = current_time - self.last_retry_time
        
        # Only log disconnections on first attempt or after significant delays
        if self.current_retries == 0 or time_since_last_retry >= self.max_retry_delay:
            log.info("[TikTokBridge] Disconnected from TikTok bridge")
        
        self.is_connected = False
        
    def send_response(self, gift_data: Dict[str, Any], action: str) -> None:
        """Send a response back to the bridge (optional)"""
        if not self.is_connected or not self.ws:
            return
            
        response = {
            'type': 'response',
            'giftProcessed': gift_data.get('gift', 'unknown'),
            'user': gift_data.get('user', 'unknown'),
            'action': action,
            'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S.000Z', time.gmtime())
        }
        
        try:
            self.ws.send(json.dumps(response))
            log.debug(f"[TikTokBridge] Sent response to bridge: {action}")
        except Exception as e:
            log.error(f"Failed to send response to bridge: {e}")


# Global instance
_bridge_client: Optional[TikTokBridgeClient] = None


def get_bridge_client() -> TikTokBridgeClient:
    """Get the global bridge client instance"""
    global _bridge_client
    if _bridge_client is None:
        _bridge_client = TikTokBridgeClient()
    return _bridge_client
