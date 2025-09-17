"""
TikTok Bridge Cheat Commands
Provides cheat commands for managing the TikTok bridge connection
"""

from sims4communitylib.utils.common_log_registry import CommonLogRegistry
from sims4communitylib.services.commands.common_console_command import CommonConsoleCommand, \
    CommonConsoleCommandArgument
from sims4communitylib.services.commands.common_console_command_output import CommonConsoleCommandOutput

from sims4communitylib.utils.sims.common_sim_utils import CommonSimUtils
from sims_tik_tok_mod.modinfo import ModInfo
from sims_tik_tok_mod.tiktok_bridge_client import get_bridge_client
from sims_tik_tok_mod.utils.cas_utils import TikTokCASUtils
from sims_tik_tok_mod.utils.vfx_utils import TikTokVFXUtils
from sims_tik_tok_mod.utils.animation_utils import TikTokAnimationUtils
from sims_tik_tok_mod.utils.pose_player_utils import TikTokPosePlayerUtils

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

    @staticmethod
    @CommonConsoleCommand(
        ModInfo.get_identity(),
        'tiktok.test_cas',
        'Test creating a new sim and opening CAS',
        command_arguments=(
            CommonConsoleCommandArgument('username', 'str', 'TestUser', is_optional=True),
        ),
        show_with_help_command=False
    )
    def _tiktok_test_cas_cheat(output: CommonConsoleCommandOutput, username: str = 'TestUser'):
        """Cheat command to test CAS opening with a new sim"""
        try:
            output(f"🎮 Creating new sim for {username} and opening CAS...")
            log.info(f"Test CAS command: Creating sim for {username}")
            
            success = TikTokCASUtils.create_sim_and_open_cas(username)
            
            if success:
                output(f"✅ Successfully created sim and initiated CAS opening for {username}!")
                output("CAS should open shortly once the sim is fully loaded...")
                log.info("Test CAS command: Success")
            else:
                output("❌ Failed to create sim or open CAS")
                log.error("Test CAS command: Failed")
                
        except Exception as e:
            output(f"❌ Error during CAS test: {e}")
            log.error(f"Test CAS cheat command error: {e}")

    @staticmethod
    @CommonConsoleCommand(
        ModInfo.get_identity(),
        'tiktok.test_animal',
        'Test creating a non-household animal sim that hangs around',
        command_arguments=(
            CommonConsoleCommandArgument('pet_name', 'str', 'TestPet Buddy', is_optional=True),
            CommonConsoleCommandArgument('animal_type', 'str', 'dog', is_optional=True),
        ),
        show_with_help_command=False
    )
    def _tiktok_test_animal_cheat(output: CommonConsoleCommandOutput, pet_name: str = 'TestPet Buddy', animal_type: str = 'dog'):
        """Cheat command to test creating a non-household animal sim"""
        try:
            output(f"🐕 Creating non-household {animal_type} '{pet_name}' that will hang around...")
            log.info(f"Test animal command: Creating {animal_type} named {pet_name}")
            
            success = TikTokCASUtils.create_non_household_animal_sim(pet_name, animal_type)
            
            if success:
                output(f"✅ Successfully created {animal_type} '{pet_name}' that will hang around the lot!")
                output("The animal should appear on your lot and behave as if they belong without being in your household.")
                log.info("Test animal command: Success")
            else:
                output(f"❌ Failed to create non-household {animal_type}")
                log.error("Test animal command: Failed")
                
        except Exception as e:
            output(f"❌ Error during animal creation test: {e}")
            log.error(f"Test animal cheat command error: {e}")

    @staticmethod
    @CommonConsoleCommand(
        ModInfo.get_identity(),
        'tiktok.test_vfx',
        'Test playing a VFX on a sim',
        command_arguments=(
            CommonConsoleCommandArgument('vfx_name', 'str', 'vfx_name', is_optional=True),
            CommonConsoleCommandArgument('joint_name', 'str', 'joint_name', is_optional=True, default_value='b__Head__'),
        ),
        show_with_help_command=False
    )
    def _tiktok_test_vfx_cheat(output: CommonConsoleCommandOutput, vfx_name: str = 'ep1_givebirth_alien', joint_name: str = 'b__Head__'):
        """Cheat command to test playing a VFX on a sim"""
        try:
            output(f"🐕 Playing VFX {vfx_name}")
            log.info(f"Test VFX command: Playing VFX {vfx_name}")
            
            success = TikTokVFXUtils.play_one_shot_on_sim(vfx_name, joint_name)
            
            if success:
                output(f"✅ Successfully played VFX {vfx_name}")
                output("The VFX should appear on the sim.")
                log.info("Test VFX command: Success")
            else:
                output(f"❌ Failed to play VFX {vfx_name}")
                log.error("Test VFX command: Failed")
                
        except Exception as e:
            output(f"❌ Error during VFX test: {e}")
            log.error(f"Test VFX cheat command error: {e}")

    @staticmethod
    @CommonConsoleCommand(
        ModInfo.get_identity(),
        'tiktok.spin_thumbs_up',
        'Make the sim do a spin followed by a thumbs up gesture',
        show_with_help_command=False
    )
    def _tiktok_spin_thumbs_up_cheat(output: CommonConsoleCommandOutput):
        """Cheat command to make sim do spin + thumbs up"""
        try:
            output("🌪️ Making sim do a spin and thumbs up...")
            log.info("Spin thumbs up command: Starting animation sequence")
            
            success = TikTokAnimationUtils.play_spin_and_thumbs_up()
            
            if success:
                output("✅ Successfully started spin and thumbs up animation sequence!")
                output("The sim should spin and then give a thumbs up gesture.")
                log.info("Spin thumbs up command: Success")
            else:
                output("❌ Failed to start spin and thumbs up animation sequence")
                log.error("Spin thumbs up command: Failed")
                
        except Exception as e:
            output(f"❌ Error during spin and thumbs up: {e}")
            log.error(f"Spin thumbs up cheat command error: {e}")

    @staticmethod
    @CommonConsoleCommand(
        ModInfo.get_identity(),
        'tiktok.spin_heart',
        'Make the sim do a spin followed by a hand heart gesture',
        show_with_help_command=False
    )
    def _tiktok_spin_heart_cheat(output: CommonConsoleCommandOutput):
        """Cheat command to make sim do spin + hand heart"""
        try:
            output("💖 Making sim do a spin and hand heart...")
            log.info("Spin heart command: Starting animation sequence")
            
            success = TikTokAnimationUtils.play_spin_and_heart_hand()
            
            if success:
                output("✅ Successfully started spin and hand heart animation sequence!")
                output("The sim should spin and then make a hand heart gesture.")
                log.info("Spin heart command: Success")
            else:
                output("❌ Failed to start spin and hand heart animation sequence")
                log.error("Spin heart command: Failed")
                
        except Exception as e:
            output(f"❌ Error during spin and hand heart: {e}")
            log.error(f"Spin heart cheat command error: {e}")

    @staticmethod
    @CommonConsoleCommand(
        ModInfo.get_identity(),
        'tiktok.spin',
        'Make the sim do just a spin animation',
        show_with_help_command=False
    )
    def _tiktok_spin_cheat(output: CommonConsoleCommandOutput):
        """Cheat command to make sim do just a spin"""
        try:
            output("🌪️ Making sim do a spin...")
            log.info("Spin command: Starting spin animation")
            
            success = TikTokAnimationUtils.play_single_spin()
            
            if success:
                output("✅ Successfully started spin animation!")
                output("The sim should do a spinning motion.")
                log.info("Spin command: Success")
            else:
                output("❌ Failed to start spin animation")
                log.error("Spin command: Failed")
                
        except Exception as e:
            output(f"❌ Error during spin: {e}")
            log.error(f"Spin cheat command error: {e}")

    @staticmethod
    @CommonConsoleCommand(
        ModInfo.get_identity(),
        'tiktok.test_animation',
        'Test playing a specific animation by name',
        command_arguments=(
            CommonConsoleCommandArgument('animation_name', 'str', 'a_dance_stepSpin_x', is_optional=True),
        ),
        show_with_help_command=False
    )
    def _tiktok_test_animation_cheat(output: CommonConsoleCommandOutput, animation_name: str = 'a_dance_stepSpin_x'):
        """Cheat command to test playing a specific animation by name"""
        try:
            output(f"🎭 Testing animation: {animation_name}")
            log.info(f"Test animation command: Playing {animation_name}")
            
            success = TikTokAnimationUtils.play_animation_by_name(
                TikTokAnimationUtils.get_active_sim(), # type: ignore[reportAssignmentType]
                animation_name
            )
            
            if success:
                output(f"✅ Successfully started animation: {animation_name}")
                log.info("Test animation command: Success")
            else:
                output(f"❌ Failed to start animation: {animation_name}")
                log.error("Test animation command: Failed")
                
        except Exception as e:
            output(f"❌ Error during animation test: {e}")
            log.error(f"Test animation cheat command error: {e}")

    @staticmethod
    @CommonConsoleCommand(
        ModInfo.get_identity(),
        'tiktok.pose.direct',
        'Directly execute a pose using game commands',
        command_arguments=(
            CommonConsoleCommandArgument('pose_name', 'str', 'pose_name_here', is_optional=False),
        ),
        show_with_help_command=False
    )
    def _tiktok_direct_pose_cheat(output: CommonConsoleCommandOutput, pose_name: str):
        """Cheat command to directly execute a pose using game command system"""
        try:
            output(f"🎭 Attempting direct pose execution: {pose_name}")
            log.info(f"Direct pose command: Executing {pose_name}")

            sim_info = CommonSimUtils.get_active_sim_info()
            if not sim_info:
                output("❌ No active sim found")
                log.error("Direct pose command: No active sim")
                return
            
            try:
                output("🔄 Trying interaction push method...")
                success = TikTokPosePlayerUtils.play_pose_by_name(sim_info, pose_name)
                if success:
                    output("✅ Interaction push method succeeded")
                else:
                    output("❌ Interaction push method failed")
                    
            except Exception as interaction_error:
                log.error(f"Interaction push failed: {interaction_error}")
                output(f"❌ Interaction push error: {interaction_error}")
        except Exception as e:
            output(f"❌ Error during direct pose execution: {e}")
            log.error(f"Direct pose cheat command error: {e}")
