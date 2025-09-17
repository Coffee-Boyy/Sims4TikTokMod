from sims.sim import Sim
from sims4.hash_util import hash32
from sims.sim_info import SimInfo
from _math import Vector3
from typing import Tuple, Optional
from sims_tik_tok_mod.modinfo import ModInfo
from sims4communitylib.utils.common_log_registry import CommonLogRegistry
from sims4communitylib.utils.sims.common_sim_utils import CommonSimUtils

# Core effect player
from vfx import PlayEffect

log = CommonLogRegistry.get().register_log(ModInfo.get_identity(), 'SimsTikTokModVFX')  # type: ignore[attr-defined]
log.enable()

class TikTokVFXUtils:
    """Convenience helpers to play attached VFX on a Sim."""

    # Replace these with actual VFX names you like (discover via Effect Player in S4S)
    PRESET_EFFECTS = {
        'confetti': 'confettistreamershort',   # placeholder name
        'hearts': 'heart_shape_stars',         # placeholder name
        'sparkles': 'vfx_sparkles_loop_short',    # placeholder name
        'burst': 'vfx_magic_burst_short',         # placeholder name
    }

    @staticmethod
    def _resolve_sim(sim_or_info):
        """Return a live Sim instance from either a Sim or SimInfo."""
        if isinstance(sim_or_info, SimInfo):
            sim = sim_or_info.get_sim_instance()
        else:
            sim = sim_or_info
        if sim is None:
            log.error('TikTokVFXUtils: Could not resolve a live Sim instance.')
        return sim

    @staticmethod
    def play_one_shot_on_sim(
        effect_name: str,
        joint_name: str = 'b__Head__',
        offset: Optional[Tuple[float, float, float]] = (0.0, 0.0, 0.0),
    ) -> bool:
        """
        Fire-and-forget one-shot effect attached to a Sim joint.
        Many 'burst' or 'pop' style effects stop by themselves.

        - joint_name: a bone/slot string that hashes to a joint (e.g., 'b__Head__', '_FX_')
        - offset: optional positional offset from the joint
        """

        try:
            target: Sim = CommonSimUtils.get_active_sim() # type: ignore[reportAssignmentType]
            transform_override = None
            joint_hash = hash32(joint_name) if joint_name else PlayEffect.JOINT_NAME_CURRENT_POSITION

            if offset is not None:
                transform_override = Vector3(offset[0], offset[1], offset[2])

            vfx = PlayEffect(
                target=target, # type: ignore[reportAssignmentType]
                effect_name=effect_name,
                joint_name=joint_hash,
                target_joint_offset=transform_override,
                play_immediate=True
            )
            vfx.start_one_shot()
            
            return True
        except Exception as ex:
            log.error(f'Failed to play one-shot VFX "{effect_name}": {ex}')
            return False

    @staticmethod
    def start_loop_on_sim(
        sim_or_info,
        effect_name: str,
        joint_name: str = 'b__Head__',
        offset: Optional[Tuple[float, float, float]] = (0.0, 0.2, 0.0),
        play_immediate: bool = True
    ):
        """
        Start a looping effect attached to a Sim joint.
        Returns the running PlayEffect instance which you must later stop with .stop().

        Note: Only use for effects that are intended to loop. For bursts, prefer play_one_shot_on_sim.
        """
        sim = TikTokVFXUtils._resolve_sim(sim_or_info)
        if sim is None:
            return None

        try:
            joint_hash = hash32(joint_name) if joint_name else PlayEffect.JOINT_NAME_CURRENT_POSITION
            vfx_kwargs = {
                'target': sim,
                'effect_name': effect_name,
                'joint_name': joint_hash,
                'play_immediate': play_immediate
            }
            if offset is not None:
                vfx_kwargs['target_joint_offset'] = Vector3(offset[0], offset[1], offset[2])

            vfx = PlayEffect(**vfx_kwargs)
            vfx.start()
            return vfx
        except Exception as ex:
            log.error(f'Failed to start loop VFX "{effect_name}" on {sim}: {ex}')
            return None

    @staticmethod
    def stop(vfx_instance, immediate: bool = False):
        """Stop a previously started loop effect."""
        try:
            if vfx_instance is not None:
                vfx_instance.stop(immediate=immediate)
        except Exception as ex:
            log.error(f'Failed to stop VFX: {ex}')