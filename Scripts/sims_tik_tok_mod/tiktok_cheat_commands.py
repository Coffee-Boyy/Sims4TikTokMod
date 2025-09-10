"""
TikTok Bridge Cheat Commands
Provides cheat commands for managing the TikTok bridge connection
"""

from sims4communitylib.utils.common_log_registry import CommonLogRegistry
from sims4communitylib.utils.sims.common_sim_utils import CommonSimUtils
from sims4communitylib.events.event_handling.common_event_registry import CommonEventRegistry
from sims4communitylib.events.zone_spin.events.zone_late_load import S4CLZoneLateLoadEvent
from sims4communitylib.services.commands.common_console_command import CommonConsoleCommand, \
    CommonConsoleCommandArgument
from sims4communitylib.services.commands.common_console_command_output import CommonConsoleCommandOutput

from sims_tik_tok_mod.modinfo import ModInfo
from sims_tik_tok_mod.tiktok_bridge_client import get_bridge_client

# Create a logger for this module
log = CommonLogRegistry.get().register_log(ModInfo.get_identity(), 'TikTokCheatCommands')
log.enable()


class TikTokCheatCommands:
    """Cheat commands for TikTok bridge management"""

    @staticmethod
    @CommonConsoleCommand(
        ModInfo.get_identity(),
        'tiktok.reconnect',
        'Force reconnection to the TikTok bridge service',
        show_with_help_command=False
    )
    def _tiktok_reconnect_cheat(output: CommonConsoleCommandOutput):
        """Cheat command to force reconnection to the bridge service"""
        try:
            output("🔄 Attempting to reconnect to TikTok bridge service...")
            log.info("Cheat command: Forcing TikTok bridge reconnection")
            
            bridge_client = get_bridge_client()
            success = bridge_client.force_reconnect()
            
            if success:
                output("✅ Reconnection attempt initiated successfully!")
                log.info("Cheat command: Reconnection attempt initiated")
            else:
                output("❌ Failed to initiate reconnection attempt")
                log.error("Cheat command: Failed to initiate reconnection")
                
        except Exception as e:
            output(f"❌ Error during reconnection attempt: {e}")
            log.error(f"Cheat command error: {e}")

    @staticmethod
    @CommonConsoleCommand(
        ModInfo.get_identity(),
        'tiktok.status',
        'Show TikTok bridge connection status',
        show_with_help_command=False
    )
    def _tiktok_status_cheat(output: CommonConsoleCommandOutput):
        """Cheat command to show bridge connection status"""
        try:
            bridge_client = get_bridge_client()
            
            output("📊 TikTok Bridge Status:")
            output(f"   🔗 Connected: {'✅ Yes' if bridge_client.is_connected else '❌ No'}")
            output(f"   🔄 Running: {'✅ Yes' if bridge_client.is_running else '❌ No'}")
            output(f"   🌐 URL: {bridge_client.url}")
            output(f"   🔁 Auto-reconnect: {'✅ Enabled' if bridge_client.auto_reconnect_enabled else '❌ Disabled'}")
            output(f"   ⏱️  Auto-reconnect interval: {bridge_client.auto_reconnect_interval}s")
            output(f"   🔢 Current retries: {bridge_client.current_retries}")
            
            if bridge_client.last_successful_connection > 0:
                import time
                time_since_connection = int(time.time() - bridge_client.last_successful_connection)
                output(f"   ⏰ Last successful connection: {time_since_connection}s ago")
            else:
                output("   ⏰ Last successful connection: Never")
                
        except Exception as e:
            output(f"❌ Error getting status: {e}")
            log.error(f"Status cheat command error: {e}")

    @staticmethod
    @CommonConsoleCommand(
        ModInfo.get_identity(),
        'tiktok.toggle_auto_reconnect',
        'Toggle automatic reconnection on/off',
        show_with_help_command=False
    )
    def _tiktok_toggle_auto_reconnect_cheat(output: CommonConsoleCommandOutput):
        """Cheat command to toggle auto-reconnection"""
        try:
            bridge_client = get_bridge_client()
            bridge_client.auto_reconnect_enabled = not bridge_client.auto_reconnect_enabled
            
            status = "enabled" if bridge_client.auto_reconnect_enabled else "disabled"
            output(f"🔄 Auto-reconnection {status}")
            log.info(f"Cheat command: Auto-reconnection {status}")
            
        except Exception as e:
            output(f"❌ Error toggling auto-reconnection: {e}")
            log.error(f"Toggle auto-reconnect cheat command error: {e}")

    @staticmethod
    @CommonConsoleCommand(
        ModInfo.get_identity(),
        'tiktok.start',
        'Start the TikTok bridge client',
        show_with_help_command=False
    )
    def _tiktok_start_cheat(output: CommonConsoleCommandOutput):
        """Cheat command to start the bridge client"""
        try:
            bridge_client = get_bridge_client()
            
            if bridge_client.is_running:
                output("⚠️  TikTok bridge client is already running")
                return
                
            output("🚀 Starting TikTok bridge client...")
            success = bridge_client.start()
            
            if success:
                output("✅ TikTok bridge client started successfully!")
                log.info("Cheat command: Bridge client started")
            else:
                output("❌ Failed to start TikTok bridge client")
                log.error("Cheat command: Failed to start bridge client")
                
        except Exception as e:
            output(f"❌ Error starting bridge client: {e}")
            log.error(f"Start cheat command error: {e}")

    @staticmethod
    @CommonConsoleCommand(
        ModInfo.get_identity(),
        'tiktok.stop',
        'Stop the TikTok bridge client',
        show_with_help_command=False
    )
    def _tiktok_stop_cheat(output: CommonConsoleCommandOutput):
        """Cheat command to stop the bridge client"""
        try:
            bridge_client = get_bridge_client()
            
            if not bridge_client.is_running:
                output("⚠️  TikTok bridge client is not running")
                return
                
            output("🛑 Stopping TikTok bridge client...")
            bridge_client.stop()
            output("✅ TikTok bridge client stopped")
            log.info("Cheat command: Bridge client stopped")
            
        except Exception as e:
            output(f"❌ Error stopping bridge client: {e}")
            log.error(f"Stop cheat command error: {e}")
