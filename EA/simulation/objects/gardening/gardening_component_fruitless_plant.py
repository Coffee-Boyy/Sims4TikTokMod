from __future__ import annotationsfrom typing import TYPE_CHECKINGif TYPE_CHECKING:
    from typing import *
    from objects.game_object import GameObject
    from notebook.notebook_entry import NotebookEntryfrom objects.components import types, componentmethod_with_fallbackimport objects.components.typesfrom objects.gardening.gardening_component_base_plant import _GardeningBasePlantComponentfrom objects.gardening.gardening_tuning import GardeningTuningfrom protocolbuffers import SimObjectAttributes_pb2 as protocolsimport servicesimport sims4.loglogger = sims4.log.Logger('Gardening', default_owner='swhitehurst')
class GardeningFruitlessPlantComponent(_GardeningBasePlantComponent, component_name=objects.components.types.GARDENING_COMPONENT, persistence_key=protocols.PersistenceMaster.PersistableData.GardeningComponent):

    def __init__(self, *args, **kwargs) -> 'None':
        super().__init__(*args, **kwargs)
        self._seed_data = None

    @property
    def root_stock(self) -> 'Optional[GameObject]':
        if not self._seed_data:
            return
        return self._seed_data

    def can_splice_with(self, shoot:'GameObject') -> 'bool':
        return False

    def on_add(self, *args, **kwargs) -> 'None':
        animal_service = services.animal_service()
        if animal_service is not None:
            animal_service.add_weed_eligible_plant(self.owner)
        return super().on_add(*args, **kwargs)

    def on_remove(self, *args, **kwargs) -> 'None':
        animal_service = services.animal_service()
        if animal_service is not None:
            animal_service.remove_weed_eligible_plant(self.owner)
        super().on_remove(*args, **kwargs)

    def add_fruit(self, fruit:'GameObject', sprouted_from:'bool'=False) -> 'None':
        if sprouted_from:
            self._apply_inherited_state(fruit)
        self._set_root(fruit)
        self.update_hovertip()

    def _apply_inherited_state(self, seed_object:'GameObject') -> 'None':
        inherited_state = GardeningTuning.INHERITED_STATE
        inherited_state_value = seed_object.get_state(inherited_state)
        self.owner.set_state(inherited_state, inherited_state_value)

    def _set_root(self, seed_object:'GameObject') -> 'None':
        if seed_object is not None:
            seed_gardening_component = seed_object.get_component(types.GARDENING_COMPONENT)
            if seed_gardening_component is not None:
                self._seed_data = seed_object

    @componentmethod_with_fallback(lambda : None)
    def get_notebook_information(self, reference_notebook_entry:'NotebookEntry', notebook_sub_entries:'List[GameObject]') -> 'Tuple[NotebookEntry, ...]':
        notebook_entry = reference_notebook_entry(self.owner.definition.id)
        return (notebook_entry,)
