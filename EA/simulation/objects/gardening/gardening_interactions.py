from __future__ import annotationsfrom objects.components.types import GARDENING_COMPONENTfrom interactions.base.picker_interaction import ObjectPickerInteractionfrom interactions.base.super_interaction import SuperInteractionfrom objects.gardening.gardening_tuning import GardeningTuningfrom sims4.utils import flexmethodfrom singletons import DEFAULTimport event_testingimport sims4from typing import TYPE_CHECKINGif TYPE_CHECKING:
    from typing import *
    from interactions.base.interaction import Interaction
    from interactions.context import InteractionContext
    from objects.game_object import GameObject
    from scheduling import Timelinelogger = sims4.log.Logger('Gardening Interactions', default_owner='swhitehurst')
class GardeningSpliceInteraction(SuperInteraction):

    def _run_interaction_gen(self, timeline:'Timeline'):
        result = yield from super()._run_interaction_gen(timeline)
        if result:
            gardening_component = self.target.get_component(GARDENING_COMPONENT)
            if gardening_component is None:
                logger.error('{} target has no Gardening Component', self)
                return False
            shoot = gardening_component.create_shoot()
            try:
                if shoot is not None and self.sim.inventory_component.player_try_add_object(shoot):
                    shoot.update_ownership(self.sim.sim_info)
                    shoot = None
                    return True
            finally:
                if shoot is not None:
                    shoot.destroy(source=self, cause='Failed to add shoot to player inventory.')
        return False

class GardeningGraftPickerInteraction(ObjectPickerInteraction):

    @flexmethod
    def _get_objects_gen(cls, inst:'Interaction', target:'GameObject', context:'InteractionContext', **kwargs):
        gardening_component = target.get_component(GARDENING_COMPONENT)
        if gardening_component is None:
            logger.error('{} target has no Gardening Component', inst or cls)
            return
        if not gardening_component.is_plant:
            logger.error('{} target is not a plant', inst or cls)
            return
        for shoot in context.sim.inventory_component:
            if gardening_component.can_splice_with(shoot):
                yield shoot

class GardeningGraftInteraction(SuperInteraction):

    @flexmethod
    def test(cls, inst:'Interaction', context:'InteractionContext'=DEFAULT, **kwargs):
        inst_or_cls = inst if inst is not None else cls
        if inst is not None and inst.carry_target is None:
            return event_testing.results.TestResult(False, 'Carry target of grafting shoot is None.')
        return super(__class__, inst_or_cls).test(context=context, **kwargs)

    def _run_interaction_gen(self, timeline:'Timeline'):
        result = yield from super()._run_interaction_gen(timeline)
        if result:
            shoot = self.carry_target
            gardening_component = self.target.get_component(GARDENING_COMPONENT)
            if gardening_component is None:
                logger.error('{} target has no Gardening Component', self)
                return False
            inventory = shoot.get_inventory()
            if inventory is None:
                logger.error('{} target does not belong to an inventory', self)
                return False
            if not inventory.try_move_object_to_hidden_inventory(shoot):
                logger.error('Tried hiding the shoot object, {}, but failed.', shoot)
                return False
            else:
                gardening_component.add_fruit(shoot)
                self.target.set_state(GardeningTuning.SPLICED_STATE_VALUE.state, GardeningTuning.SPLICED_STATE_VALUE)
                shoot.transient = True
                return True
        return False
