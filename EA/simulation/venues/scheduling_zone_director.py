from __future__ import annotationsfrom typing import TYPE_CHECKINGif TYPE_CHECKING:
    from typing import *
    from sims4 import PropertyStreamWriter
    from protocolbuffers.GameplaySaveData_pb2 import AmbientSourceData, OpenStreetDirectorData, ZoneDirectorDatafrom celebrity_fans.fan_zone_director_mixin import FanZoneDirectorMixinfrom sims4.resources import Typesfrom sims4.tuning.instances import TunedInstanceMetaclassfrom sims4.tuning.tunable import TunableSimMinute, TunableList, TunableTuple, TunableEnumEntry, TunableVariant, Tunable, TunableReferencefrom sims4.tuning.tunable_base import GroupNamesfrom situations.additional_situation_sources import HolidayWalkbys, ZoneModifierSituations, NarrativeSituationsfrom situations.complex.yoga_class import YogaClassScheduleMixinfrom situations.situation_curve import SituationCurve, ShiftlessDesiredSituationsfrom situations.situation_guest_list import SituationGuestListfrom situations.situation_shifts import SituationShiftsfrom situations.situation_types import SituationSerializationOptionfrom venues.object_based_situation_zone_director import ObjectBasedSituationZoneDirectorMixinfrom zone_director import ZoneDirectorBaseimport alarmsimport clockimport enumimport servicesimport sims4.loglogger = sims4.log.Logger('ZoneDirectorScheduling')
class SchedulingZoneDirectorMixin:

    @staticmethod
    def _verify_situations_on_load_callback(instance_class, tunable_name, source, value, **kwargs):
        for situation in value:
            if situation.situation_serialization_option != SituationSerializationOption.DONT:
                logger.error('Situation {} in situations on load tuning for zone director {} has an invalid persistence option. Only DONT is acceptable.', situation, instance_class)

    INSTANCE_TUNABLES = {'situations_on_load': TunableList(description="\n            Situations that are always started when the zone director loads and\n            are only shut down by the zone director when the zone director shuts\n            down (although they can still end by other means). Because these\n            situations are always restarted, it is invalid to schedule\n            situations with a positive persistence option here (ask a GPE if you\n            need to determine a situation's persistence option).\n            ", tunable=TunableReference(manager=services.get_instance_manager(Types.SITUATION), pack_safe=True), verify_tunable_callback=_verify_situations_on_load_callback, tuning_group=GroupNames.SITUATION)}

    def _init_situation_shifts(self) -> 'None':
        shift_data = {}
        for key in SituationShifts.FACTORY_TUNABLES:
            shift_data[key] = getattr(self, key)
        self.situation_shifts = SituationShifts(**shift_data)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._situations_on_load_ids = []
        self._init_situation_shifts()

    def on_startup(self) -> 'None':
        super().on_startup()
        self.situation_shifts.on_startup()

    def on_shutdown(self):
        self.destroy_shifts()
        self.situation_shifts.on_shutdown()
        situation_manager = services.get_zone_situation_manager()
        for situation_id in self._situations_on_load_ids:
            situation_manager.destroy_situation_by_id(situation_id)
        self._situations_on_load_ids.clear()
        super().on_shutdown()

    def destroy_shifts(self):
        self.situation_shifts.destroy_shifts()

    def create_situations_during_zone_spin_up(self):
        self.situation_shifts.create_situations_during_zone_spin_up()
        if not self._situations_on_load_ids:
            situation_manager = services.get_zone_situation_manager()
            for situation in self.situations_on_load:
                situation_id = situation_manager.create_situation(situation, user_facing=False, creation_source='Situations on load')
                self._situations_on_load_ids.append(situation_id)
        super().create_situations_during_zone_spin_up()

    def _save_custom_zone_director(self, zone_director_proto, writer):
        self.situation_shifts.save_situation_shifts(zone_director_proto)
        super()._save_custom_zone_director(zone_director_proto, writer)

    def _load_custom_zone_director(self, zone_director_proto, reader):
        self.situation_shifts.load_situation_shifts(zone_director_proto)
        super()._load_custom_zone_director(zone_director_proto, reader)

    def save_situation_shifts(self, proto:'Union[ZoneDirectorData, OpenStreetDirectorData, AmbientSourceData]', writer:'Optional[PropertyStreamWriter]'=None, validate:'bool'=True) -> 'None':
        self.situation_shifts.save_situation_shifts(proto, validate=validate)

    def load_situation_shifts(self, proto, reader=None):
        self.situation_shifts.load_situation_shifts(proto)

    def get_all_situations_from_shifts(self):
        return self.situation_shifts.get_all_situations()

class SchedulingZoneDirector(YogaClassScheduleMixin, FanZoneDirectorMixin, ObjectBasedSituationZoneDirectorMixin, SchedulingZoneDirectorMixin, ZoneDirectorBase):
    pass
