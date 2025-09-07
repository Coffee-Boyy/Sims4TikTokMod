from __future__ import annotationsimport sims4from interactions import ParticipantTypeObjectfrom interactions.liability import Liabilityfrom sims4.tuning.tunable import TunableEnumEntry, HasTunableFactory, AutoFactoryInit, Tunablefrom typing import TYPE_CHECKINGif TYPE_CHECKING:
    from typing import *
    from interactions.base.interaction import Interactionlogger = sims4.log.Logger('Object Liabilities', default_owner='skorman')
class TemporaryHiddenInventoryTransferLiability(Liability, HasTunableFactory, AutoFactoryInit):
    LIABILITY_TOKEN = 'TemporaryHiddenInventoryTransferLiability'
    FACTORY_TUNABLES = {'object': TunableEnumEntry(description='\n            The object that will be temporarily moved from an inventory to its \n            associated hidden inventory.\n            ', tunable_type=ParticipantTypeObject, default=ParticipantTypeObject.PickedObject), 'move_entire_stack': Tunable(description='\n            When set to True, all objects within the same stack as the tuned object\n            will additionally be moved from an inventory to its associated \n            hidden inventory.\n            Otherwise, when set to False, only moves the tuned object.\n            ', tunable_type=bool, default=False)}

    def __init__(self, interaction, **kwargs):
        super().__init__(**kwargs)
        self._obj = interaction.get_participant(self.object)
        self._stack_id = None
        self._inventory = None

    def should_transfer(self, continuation:'Interaction') -> 'bool':
        return False

    def _return_obj(self) -> 'None':
        if self._inventory is None:
            return
        if self.move_entire_stack:
            if self._stack_id is None:
                logger.error('Object {} failed to get an stack id when it was added to this object liability.', self._obj)
                return
            self._inventory.try_move_hidden_object_stack_to_inventory(self._stack_id)
        else:
            if self._obj is None:
                return
            self._inventory.try_move_hidden_object_to_inventory(self._obj)

    def on_add(self, interaction:'Interaction') -> 'None':
        if self._obj is None:
            return
        self._inventory = self._obj.get_inventory()
        if self._inventory is None:
            logger.error('Object {} is not in an inventory, so it cannot be moved to the hidden inventory', self._obj)
            return
        if self.move_entire_stack:
            self._stack_id = self._obj.inventoryitem_component.get_stack_id()
            if not self._inventory.try_move_object_stack_to_hidden_inventory(self._stack_id):
                logger.error('Tried moving object stack {} with object {} to hidden inventory, but failed.', self._stack_id, self._obj)
        elif not self._inventory.try_move_object_to_hidden_inventory(self._obj):
            logger.error('Tried moving object {} to hidden inventory, but failed.', self._obj)

    def on_reset(self) -> 'None':
        self._return_obj()

    def release(self) -> 'None':
        self._return_obj()
