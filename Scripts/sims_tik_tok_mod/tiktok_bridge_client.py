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
log = CommonLogRegistry.get().register_log(ModInfo.get_identity(), 'TikTokBridge')  # type: ignore[attr-defined]
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
        
        # Callback for when action events are received
        self.on_action_callback: Optional[Callable[[Dict[str, Any]], None]] = None
        
        # Callback for when like events are received
        self.on_like_callback: Optional[Callable[[Dict[str, Any]], None]] = None
        
        # Callback for connection status changes
        self.on_connection_callback: Optional[Callable[[bool, str], None]] = None
        
        # Connection retry settings
        self.max_retries = 5
        self.retry_delay = 5  # seconds
        self.max_retry_delay = 60  # maximum 60 seconds between retries
        self.current_retries = 0
        self.last_retry_time = 0  # timestamp of last retry attempt
        
        # Auto-reconnection settings
        self.auto_reconnect_enabled = True
        self.auto_reconnect_interval = 30  # seconds
        self.auto_reconnect_thread: Optional[threading.Thread] = None
        self.last_successful_connection = 0  # timestamp of last successful connection
        
    def set_action_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Set the callback function to be called when action events are received"""
        self.on_action_callback = callback
        
    def set_like_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Set the callback function to be called when like events are received"""
        self.on_like_callback = callback
        
    def set_connection_callback(self, callback: Callable[[bool, str], None]) -> None:
        """Set the callback function to be called when connection status changes"""
        self.on_connection_callback = callback
        
    def start(self) -> bool:
        """Start the WebSocket client connection"""
        if not WEBSOCKET_AVAILABLE:
            log.error("[TikTokBridge] WebSocket client not available. Please install websocket-client package.")
            # Notify about websocket unavailability
            if self.on_connection_callback:
                try:
                    self.on_connection_callback(False, "WebSocket client not available")
                except Exception as e:
                    log.error(f"Error in connection callback: {e}")
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
        
        # Start auto-reconnection monitor thread
        if self.auto_reconnect_enabled:
            self.auto_reconnect_thread = threading.Thread(target=self._auto_reconnect_monitor, daemon=True)
            self.auto_reconnect_thread.start()
        
        return True
        
    def stop(self) -> None:
        """Stop the WebSocket client"""
        log.info("[TikTokBridge] Stopping TikTok bridge client...")
        self.is_running = False
        
        if self.ws:
            self.ws.close()
            
        if self.connection_thread and self.connection_thread.is_alive():
            self.connection_thread.join(timeout=5)
            
        if self.auto_reconnect_thread and self.auto_reconnect_thread.is_alive():
            self.auto_reconnect_thread.join(timeout=2)
            
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
                        # Notify about connection failure
                        if self.on_connection_callback:
                            try:
                                self.on_connection_callback(False, "Failed to connect to TikTok bridge after maximum retry attempts")
                            except Exception as e:
                                log.error(f"Error in connection callback: {e}")
                        break
                        
            except Exception as e:
                # Handle different types of connection errors
                current_time = time.time()
                time_since_last_retry = current_time - self.last_retry_time
                
                # Determine error type and create appropriate user message
                error_message = self._get_user_friendly_error_message(e)
                
                # Only log and notify on first attempt or after significant delays
                if self.current_retries == 0 or time_since_last_retry >= self.max_retry_delay:
                    log.error(f"[TikTokBridge] Connection error: {e}")
                    
                    # Notify user about the connection error (only on first attempt to avoid spam)
                    if self.current_retries == 0 and self.on_connection_callback:
                        try:
                            self.on_connection_callback(False, error_message)
                        except Exception as callback_error:
                            log.error(f"Error in connection callback: {callback_error}")
                
                self.current_retries += 1
                if self.is_running and self.current_retries < self.max_retries:
                    # Use exponential backoff with max delay of 60 seconds
                    delay = min(self.retry_delay * (2 ** (self.current_retries - 1)), self.max_retry_delay)
                    time.sleep(delay)
                    
        self.is_running = False
        self.is_connected = False
    
    def _get_user_friendly_error_message(self, error: Exception) -> str:
        """Convert technical errors into user-friendly messages"""
        error_name = type(error).__name__
        error_str = str(error).lower()
        
        if error_name == 'ConnectionRefusedError' or 'connection refused' in error_str:
            return "Cannot connect to TikTok bridge service. Make sure the bridge application is running."
        elif error_name == 'ConnectionResetError' or 'connection reset' in error_str:
            return "Connection to TikTok bridge was lost. The bridge service may have stopped."
        elif error_name == 'TimeoutError' or 'timeout' in error_str:
            return "Connection to TikTok bridge timed out. Check your network connection."
        elif 'name resolution' in error_str or 'nodename nor servname provided' in error_str:
            return "Cannot find TikTok bridge service. Check the bridge service address."
        elif 'permission denied' in error_str:
            return "Permission denied connecting to TikTok bridge. Check firewall settings."
        elif 'network is unreachable' in error_str:
            return "Network unreachable. Check your internet connection."
        else:
            # Generic fallback message for unknown errors
            return f"Failed to connect to TikTok bridge service. Error: {error_name}"
        
    def _on_open(self, ws) -> None:
        """Called when WebSocket connection is opened"""
        log.info("[TikTokBridge] ✅ Connected to TikTok bridge!")
        self.is_connected = True
        self.current_retries = 0  # Reset retry counter on successful connection
        self.last_successful_connection = time.time()  # Track successful connection time
        
        # Notify about successful connection
        if self.on_connection_callback:
            try:
                self.on_connection_callback(True, "Connected to TikTok bridge")
            except Exception as e:
                log.error(f"Error in connection callback: {e}")
        
    def _on_message(self, ws, message: str) -> None:
        """Called when a message is received from the bridge"""
        try:
            data = json.loads(message)
            event_type = data.get('type', 'unknown')
            
            log.debug(f"Received event: {event_type}")
            
            if event_type == 'sims_action' and self.on_action_callback:
                # Call the action callback
                self.on_action_callback(data)
            elif event_type == 'like' and self.on_like_callback:
                # Call the like callback
                self.on_like_callback(data)
            elif event_type == 'connection':
                log.info(f"Bridge connection message: {data.get('message', '')}")
            else:
                log.debug(f"Unhandled event type: {event_type}")
                
        except json.JSONDecodeError as e:
            log.error(f"Failed to parse message from bridge: {e}")
        except Exception as e:
            log.error(f"Error handling bridge message: {e}")
            
    def _on_error(self, ws, error) -> None:
        """Called when a WebSocket error occurs"""
        try:
            # Handle errors gracefully and provide user feedback when appropriate
            current_time = time.time()
            time_since_last_retry = current_time - self.last_retry_time
            
            # Only log errors on first attempt or after significant delays to avoid spam
            if self.current_retries == 0 or time_since_last_retry >= self.max_retry_delay:
                log.error(f"[TikTokBridge] WebSocket error: {error}")
                
                # For websocket-specific errors that occur after connection, provide user feedback
                # But only on first occurrence to avoid spam
                if self.current_retries == 0 and self.on_connection_callback:
                    error_message = self._get_user_friendly_error_message(error)
                    try:
                        self.on_connection_callback(False, error_message)
                    except Exception as callback_error:
                        log.error(f"Error in connection callback: {callback_error}")
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
        
    def send_response(self, action_data: Dict[str, Any], action_description: str) -> None:
        """Send a response back to the bridge (optional)"""
        if not self.is_connected or not self.ws:
            return
            
        response = {
            'type': 'response',
            'actionProcessed': action_data.get('action', 'unknown'),
            'user': action_data.get('user', 'unknown'),
            'description': action_description,
            'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S.000Z', time.gmtime())
        }
        
        try:
            self.ws.send(json.dumps(response))
            log.debug(f"[TikTokBridge] Sent response to bridge: {action_description}")
        except Exception as e:
            log.error(f"Failed to send response to bridge: {e}")
    
    def force_reconnect(self) -> bool:
        """Force a reconnection attempt"""
        log.info("[TikTokBridge] 🔄 Forcing reconnection to bridge service...")
        
        # Close current connection if it exists
        if self.ws:
            try:
                self.ws.close()
            except:
                pass
        
        self.is_connected = False
        self.current_retries = 0
        
        # Start a new connection attempt
        if not self.is_running:
            return self.start()
        else:
            # If already running, the auto-reconnect will handle it
            log.info("[TikTokBridge] Reconnection will be handled by auto-reconnect system")
            return True
    
    def _auto_reconnect_monitor(self) -> None:
        """Monitor connection and attempt reconnection every 30 seconds if disconnected"""
        log.info("[TikTokBridge] 🔄 Auto-reconnection monitor started (checking every 30 seconds)")
        
        while self.is_running:
            try:
                time.sleep(self.auto_reconnect_interval)
                
                if not self.is_running:
                    break
                
                # Check if we're disconnected
                if not self.is_connected:
                    current_time = time.time()
                    time_since_last_connection = current_time - self.last_successful_connection
                    
                    # Only attempt reconnection if we've been disconnected for at least 5 seconds
                    # and it's been at least 30 seconds since last successful connection
                    if time_since_last_connection >= 5:
                        log.info("[TikTokBridge] 🔄 Auto-reconnection: Attempting to reconnect...")
                        
                        # Reset retries for auto-reconnection attempt
                        self.current_retries = 0
                        
                        # The main connection loop will handle the actual reconnection
                        if not self.connection_thread or not self.connection_thread.is_alive():
                            self.connection_thread = threading.Thread(target=self._run_connection, daemon=True)
                            self.connection_thread.start()
                    
            except Exception as e:
                log.error(f"[TikTokBridge] Error in auto-reconnect monitor: {e}")
                
        log.info("[TikTokBridge] Auto-reconnection monitor stopped")


# Global instance
_bridge_client: Optional[TikTokBridgeClient] = None


def get_bridge_client() -> TikTokBridgeClient:
    """Get the global bridge client instance"""
    global _bridge_client
    if _bridge_client is None:
        _bridge_client = TikTokBridgeClient()
    return _bridge_client
