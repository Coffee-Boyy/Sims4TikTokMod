from __future__ import annotationsimport build_buyimport servicesfrom event_testing.test_events import TestEventfrom plex.plex_enums import PlexBuildingTypefrom sims4.tuning.tunable import TunableThresholdfrom sims4.tuning.tunable_base import GroupNamesfrom situations.situation_goal import SituationGoalfrom typing import TYPE_CHECKINGif TYPE_CHECKING:
    import string
    from event_testing.resolver import DataResolver
    from sims.household import Household
    from sims.sim_info import SimInfo
    from sims4 import PropertyStreamWriter
    from situations.situation_serialization import GoalSeedling
    from world.lot import Lot
    from zone import Zone
class SituationGoalLotTileCountChange(SituationGoal):
    ZONE_ID = 'zone_id'
    __annotations__['ZONE_ID'] = 'string'
    ORIGINAL_TILE_COUNT = 'original_tile_count'
    __annotations__['ORIGINAL_TILE_COUNT'] = 'string'
    test_events = (TestEvent.OnExitBuildBuy,)
    __annotations__['test_events'] = 'tuple'
    INSTANCE_TUNABLES = {'tile_count_threshold': TunableThreshold(description="\n            The threshold difference for a change in a lot's tile count.\n            \n            NOTE: This check will be skipped if the home's lot type is\n            anything other than a regular lot (an apartment for example).\n            It will also be skipped if the lot's minimum or maximum tile\n            count has already been reached. This allows players who are\n            already in either state to pass the test.\n            ", tuning_group=GroupNames.TESTS)}

    def __init__(self, *args, reader=None, **kwargs):
        super().__init__(*args, reader=reader, **kwargs)
        self._home_zone_id = None
        self._original_tile_count = None
        if reader is not None:
            self._home_zone_id = reader.read_uint64(self.ZONE_ID, None)
            self._original_tile_count = reader.read_uint64(self.ORIGINAL_TILE_COUNT, None)

    def setup(self) -> 'None':
        super().setup()
        build_buy.register_build_buy_enter_callback(self._on_build_buy_enter)
        services.get_event_manager().register(self, self.test_events)

    def _decommision(self) -> 'None':
        build_buy.unregister_build_buy_enter_callback(self._on_build_buy_enter)
        services.get_event_manager().unregister(self, self.test_events)
        super()._decommision()

    def create_seedling(self) -> 'GoalSeedling':
        seedling = super().create_seedling()
        writer = seedling.writer
        if self._home_zone_id is not None:
            writer.write_uint64(self.ZONE_ID, self._home_zone_id)
        if self._original_tile_count is not None:
            writer.write_uint64(self.ORIGINAL_TILE_COUNT, self._original_tile_count)
        return seedling

    def _run_goal_completion_tests(self, sim_info:'SimInfo', event:'TestEvent', resolver:'DataResolver') -> 'bool':
        active_lot = services.active_lot()
        if self._home_zone_id is None or active_lot is None or active_lot.zone_id != self._home_zone_id:
            return False
        building_type = services.get_plex_service().get_plex_building_type(services.current_zone_id())
        max_lot_levels = active_lot.max_allowed_level - active_lot.min_allowed_level + 1
        max_tile_count = (active_lot.size_x - 2)*(active_lot.size_z - 2)*max_lot_levels
        threshold_is_positive = self.tile_count_threshold.value >= 0
        current_tile_count = active_lot.tile_count
        delta = current_tile_count - self._original_tile_count
        perform_check = True
        if building_type != PlexBuildingType.DEFAULT and building_type != PlexBuildingType.COASTAL:
            perform_check = False
        elif threshold_is_positive:
            if current_tile_count >= max_tile_count:
                perform_check = False
        elif current_tile_count <= 0:
            perform_check = False
        if perform_check and not self.tile_count_threshold.compare(delta):
            return False
        return super()._run_goal_completion_tests(sim_info, event, resolver)

    def _on_build_buy_enter(self) -> 'None':
        household = services.active_household()
        if household is not None:
            home_zone = services.get_zone(household.home_zone_id)
            if home_zone.lot is not None:
                if self._original_tile_count is None or self._home_zone_id != home_zone.id:
                    self._original_tile_count = home_zone.lot.tile_count
                self._home_zone_id = home_zone.id
