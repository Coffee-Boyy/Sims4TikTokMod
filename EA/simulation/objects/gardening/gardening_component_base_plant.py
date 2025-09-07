from __future__ import annotationsfrom objects.components.utils.enchantment_component import EnchantmentComponentfrom protocolbuffers import SimObjectAttributes_pb2 as protocolsfrom protocolbuffers import UI_pb2 as ui_protocolsfrom objects.gardening.gardening_component import _GardeningComponentfrom objects.gardening.gardening_tuning import GardeningTuningfrom objects.hovertip import TooltipFieldsfrom objects.components.types import ENCHANTMENT_COMPONENT, GARDENING_COMPONENTimport servicesimport sims4.logfrom typing import TYPE_CHECKINGif TYPE_CHECKING:
    from typing import *
    from objects.components.state import ObjectState, ObjectStateValuelogger = sims4.log.Logger('Gardening', default_owner='swhitehurst')
class _GardeningBasePlantComponent(_GardeningComponent, component_name=GARDENING_COMPONENT, persistence_key=protocols.PersistenceMaster.PersistableData.GardeningComponent):

    @property
    def is_plant(self) -> 'bool':
        return True

    def on_add(self, *args, **kwargs) -> 'None':
        zone = services.current_zone()
        if not zone.is_zone_loading:
            gardening_service = services.get_gardening_service()
            gardening_service.add_gardening_object(self.owner)
        return super().on_add(*args, **kwargs)

    def on_remove(self, *_, **__) -> 'None':
        wisp_service = services.get_wisp_service()
        if wisp_service is not None:
            wisp_service.on_plant_removed(self.owner)
        gardening_service = services.get_gardening_service()
        gardening_service.remove_gardening_object(self.owner)

    def on_finalize_load(self):
        gardening_service = services.get_gardening_service()
        gardening_service.add_gardening_object(self.owner)

    def on_location_changed(self, old_location):
        zone = services.current_zone()
        if not zone.is_zone_loading:
            gardening_service = services.get_gardening_service()
            gardening_service.move_gardening_object(self.owner)

    def on_state_changed(self, state:'ObjectState', old_value:'ObjectStateValue', new_value:'ObjectStateValue', from_init:'bool') -> 'None':
        self.update_hovertip()
        if GardeningTuning.is_enchanted(self.owner):
            if not self.owner.has_component(ENCHANTMENT_COMPONENT):
                self.owner.add_component(EnchantmentComponent(self.owner))
        elif self.owner.has_component(ENCHANTMENT_COMPONENT):
            self.owner.remove_component(ENCHANTMENT_COMPONENT)

    def _ui_metadata_gen(self) -> 'Generator[str, Any]':
        if not self.show_gardening_tooltip():
            self.owner.hover_tip = ui_protocols.UiObjectMetadata.HOVER_TIP_DISABLED
            return
        if self.show_gardening_details():
            if self.show_evolution_in_tooltip() and self.owner.has_state(GardeningTuning.EVOLUTION_STATE):
                state_value = self.owner.get_state(GardeningTuning.EVOLUTION_STATE)
                evolution_value = state_value.range.upper_bound
                yield ('evolution_progress', evolution_value)
            if GardeningTuning.SEASONAL_STATUS_STATE is not None and self.owner.has_state(GardeningTuning.SEASONAL_STATUS_STATE):
                seasonal_status_state_value = self.owner.get_state(GardeningTuning.SEASONAL_STATUS_STATE)
                if seasonal_status_state_value is not None:
                    yield (TooltipFields.season_text.name, seasonal_status_state_value.display_name)
                    active_seasons_text = GardeningTuning.get_active_seasons_text_from_plant(self.owner.default_definition)
                    if active_seasons_text:
                        yield (TooltipFields.active_seasons_text.name, active_seasons_text)
            if self.owner.has_state(GardeningTuning.QUALITY_STATE_VALUE):
                quality_state_value = self.owner.get_state(GardeningTuning.QUALITY_STATE_VALUE)
                if quality_state_value is not None:
                    quality_value = quality_state_value.value
                    yield ('quality', quality_value)
        yield from super()._ui_metadata_gen()
