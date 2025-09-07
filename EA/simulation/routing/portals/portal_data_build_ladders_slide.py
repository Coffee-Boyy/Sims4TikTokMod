from __future__ import annotationsimport sims4from animation import get_throwaway_animation_context, animation_constantsfrom animation.arb import Arbfrom animation.asm import create_asmfrom routing import Locationfrom routing.portals.build_ladders_mixin import _BuildLaddersMixinfrom routing.portals.portal_data_base import _PortalTypeDataBasefrom routing.portals.portal_enums import PortalAlignmentfrom routing.portals.portal_location import _PortalBoneLocationfrom routing.portals.portal_tuning import PortalTypefrom routing.portals.variable_jump_mixin import _VariableJumpMixinfrom sims4.tuning.geometric import TunableVector3from sims4.tuning.tunable import OptionalTunablefrom sims4.utils import classpropertyfrom typing import TYPE_CHECKINGif TYPE_CHECKING:
    from typing import *
    from animation.animation_utils import StubActor
    from routing.portals import _PortalInstancelogger = sims4.log.Logger('BuildLaddersSlidePortalData', default_owner='bnguyen')
class _PortalTypeDataBuildLaddersSlide(_PortalTypeDataBase, _BuildLaddersMixin, _VariableJumpMixin):
    FACTORY_TUNABLES = {'slide_end_location': _PortalBoneLocation.TunableFactory(description='\n            The bone location where the slide portion of the animation ends.\n            This should be different than the portal exit location.\n            '), 'slide_end_offset': OptionalTunable(description="\n            The offset T tuned in the Animation Element's clips. This value is typically found within Sage. \n            It is added to the forward offset position of the ladder. Only tune this if you are using this  \n            portal data to go UP the ladder and observe snapping. When in doubt, contact your GPE partner.\n            ", tunable=TunableVector3(default=TunableVector3.DEFAULT_ZERO))}

    @property
    def portal_type(self):
        return PortalType.PortalType_Animate

    @property
    def requires_los_between_points(self):
        return False

    @property
    def lock_portal_on_use(self):
        return False

    @classproperty
    def discourage_portal_on_plan(cls):
        return False

    def add_portal_data(self, actor, portal_instance, is_mirrored, walkstyle):
        return self._add_variable_jump_portal_data(actor, portal_instance, is_mirrored, walkstyle)

    def get_portal_duration(self, portal_instance, is_mirrored, walkstyle, age, gender, species):
        return self._get_variable_jump_portal_duration(portal_instance, is_mirrored, species)

    def get_portal_locations(self, obj):
        return self._get_ladder_portal_locations(obj)

    def _get_arb(self, actor:'StubActor', portal_instance:'_PortalInstance', *, is_mirrored) -> 'Arb':
        arb = Arb()
        asm = create_asm(self.animation_element.asm_key, context=get_throwaway_animation_context())
        asm.set_actor(self.animation_element.actor_name, actor)
        slide_end_location = self.slide_end_location(portal_instance.obj)
        if self.climb_up_locations:
            entry_location = portal_instance.there_entry
            portal_there_exit = portal_instance.there_exit
            new_slide_end_position = sims4.math.Vector3(portal_instance.obj.position_with_forward_offset.x, portal_there_exit.position.y, portal_instance.obj.position_with_forward_offset.z)
            if self.slide_end_offset:
                new_slide_end_position += portal_instance.obj.forward*self.slide_end_offset.magnitude()
            exit_location = Location(new_slide_end_position, slide_end_location.orientation, slide_end_location.routing_surface)
            initial_translation = entry_location.position
            target_translation = new_slide_end_position
        else:
            if is_mirrored:
                new_slide_end_position = sims4.math.Vector3(slide_end_location.position.x, portal_instance.back_entry.position.y, slide_end_location.position.z)
                entry_location = Location(new_slide_end_position, slide_end_location.orientation, slide_end_location.routing_surface)
                exit_location = portal_instance.back_exit
            else:
                new_slide_end_position = sims4.math.Vector3(slide_end_location.position.x, portal_instance.there_exit.position.y, slide_end_location.position.z)
                exit_location = Location(new_slide_end_position, slide_end_location.orientation, slide_end_location.routing_surface)
                entry_location = portal_instance.there_entry
            initial_translation = sims4.math.Vector3(exit_location.position.x, entry_location.position.y, exit_location.position.z)
            target_translation = exit_location.position
        asm.set_actor_parameter(self.animation_element.actor_name, actor, animation_constants.ASM_INITIAL_TRANSLATION, initial_translation)
        asm.set_actor_parameter(self.animation_element.actor_name, actor, animation_constants.ASM_INITIAL_ORIENTATION, entry_location.orientation)
        asm.set_actor_parameter(self.animation_element.actor_name, actor, animation_constants.ASM_TARGET_TRANSLATION, target_translation)
        asm.set_actor_parameter(self.animation_element.actor_name, actor, animation_constants.ASM_TARGET_ORIENTATION, exit_location.orientation)
        asm.set_actor_parameter(self.animation_element.actor_name, actor, animation_constants.ASM_LADDER_PORTAL_ALIGNMENT, PortalAlignment.get_asm_parameter_string(self.portal_alignment))
        self.animation_element.append_to_arb(asm, arb)
        return arb
