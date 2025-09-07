from __future__ import annotationsfrom typing import TYPE_CHECKINGif TYPE_CHECKING:
    from typing import *
    from sims.sim_info import SimInfo
    from services.rabbit_hole_service import RabbitHoleService
    from protocolbuffers.FileSerialization_pb2 import SaveGameDatafrom dataclasses import dataclass, fieldfrom distributor.ops import ShowHorseCompetitionSelector, ShowHorseCompetitionResultsfrom distributor.rollback import ProtocolBufferRollbackfrom event_testing.resolver import DoubleSimResolver, SingleSimResolverfrom event_testing.tests import TunableTestSetWithTooltip, TunableTestSetfrom protocolbuffers import GameplaySaveData_pb2from protocolbuffers.Consts_pb2 import FUNDS_EVENT_COST, FUNDS_EVENET_REWARDfrom sims.sim_info_types import Speciesfrom sims4 import logfrom sims4.localization import TunableLocalizedStringFactoryfrom sims4.random import weighted_random_indexfrom sims4.resources import CompoundTypesfrom sims4.service_manager import Servicefrom sims4.tuning.tunable import TunableList, TunableTuple, Tunable, HasTunableFactory, AutoFactoryInit, TunableReference, TunableResourceKey, TunableMapping, OptionalTunablefrom sims4.tuning.tunable_base import ExportModesfrom sims4.utils import classpropertyfrom snippets import define_snippetfrom tunable_multiplier import TunableMultiplier, TunableStatisticModifierCurvefrom ui.ui_dialog_picker import UiSimPicker, UiSkillsSimPicker, SimPickerRowimport distributor.systemimport persistence_error_typesimport servicesimport sims4.resourceslogger = sims4.log.Logger('HorseCompetitions', default_owner='mjuskelis')
class HorseCompetitionPlacement(TunableTuple):

    def __init__(self, *args, **kwargs):
        super().__init__(name=TunableLocalizedStringFactory(description='\n                The name of this placement.\n                ', export_modes=ExportModes.All), narrative_description=TunableLocalizedStringFactory(description='\n                The description of this placement, used in the results\n                screen.\n                ', export_modes=ExportModes.All), icon=TunableResourceKey(description='\n                The icon image to be displayed.\n                ', default=None, resource_types=CompoundTypes.IMAGE, export_modes=ExportModes.All), large_icon=TunableResourceKey(description='\n                A large version of the icon image to be displayed.\n                ', default=None, resource_types=CompoundTypes.IMAGE, export_modes=ExportModes.All), simoleon_amount=Tunable(description='\n                The simoleon amount given when earning this reward.\n\n                Note: this amount does NOT need to be tuned in\n                the loot in order to be given.\n                ', tunable_type=int, default=0, export_modes=ExportModes.All), loots=TunableList(description='\n                The loots that will be rewarded alongside the simoleon amount.\n                ', tunable=TunableReference(description='\n                    A loot that will be rewarded.\n                    ', manager=services.get_instance_manager(sims4.resources.Types.ACTION), class_restrictions=('LootActions',)), export_modes=(ExportModes.ServerXML,)), weight=TunableMultiplier.TunableFactory(description='\n                Calculations for the weight of getting this placement in the\n                competition.\n                ', export_modes=(ExportModes.ServerXML,)), skill_multipliers=TunableList(description='\n                A list of statistic curve modifiers for skill based weights.\n                ', tunable=TunableStatisticModifierCurve.TunableFactory(description='\n                    The curve to use to calculate the multiplier.\n                    '), export_modes=(ExportModes.ServerXML,)), medal_name=TunableLocalizedStringFactory(description='\n                The name we will use for the medal itself, including the word \'medal\'.\n                For example, "Gold Medal", or "No Medal".\n                ', export_modes=ExportModes.All), results_title_text=TunableLocalizedStringFactory(description='\n                The text we will use in the results screen when we get this placement.\n                \n                For example, "First Place!", or "Try Again!".\n                ', export_modes=ExportModes.All), frame_name=Tunable(description='\n                The frame label (NOT number) from the UI .fla file(s) that we want to \n                use for this placement. Determines various colors, effects, etc.\n                ', tunable_type=str, default='', export_modes=ExportModes.All), associated_horse_trait=TunableReference(description="\n                The trait that, if present on the horse, indicates that the horse has earned this placement before.\n                NOTE: this does NOT give the horse the trait, it only looks for this trait when loading\n                the horse's data.\n                ", manager=services.get_instance_manager(sims4.resources.Types.TRAIT), export_modes=(ExportModes.ServerXML,)), **kwargs)

class HorseCompetitionSkillRequirement(TunableTuple):

    def __init__(self, *args, **kwargs):
        super().__init__(skill=TunableReference(description='\n                The skill this requirement checks against.\n                ', manager=services.get_instance_manager(sims4.resources.Types.STATISTIC), class_restrictions=('Skill',), pack_safe=True, export_modes=ExportModes.All), recommended_level=Tunable(description='\n                The recommended level for the competitor to have with this skill.\n                ', tunable_type=int, default=0, export_modes=ExportModes.All), **kwargs)

class HorseCompetition(HasTunableFactory, AutoFactoryInit):
    FACTORY_TUNABLES = {'title': TunableLocalizedStringFactory(description='\n            The title of this competition.\n            ', export_modes=ExportModes.All), 'show_title': Tunable(description='\n            Do we want to display the title for this competition?\n            ', tunable_type=bool, default=True, export_modes=ExportModes.All), 'competition_description': TunableLocalizedStringFactory(description='\n            The description of this competition.\n            ', export_modes=ExportModes.All), 'entry_fee': Tunable(description='\n            The fee that must be paid to enter the competition.\n            ', tunable_type=int, default=0, export_modes=ExportModes.All), 'sim_skill_requirements': TunableList(description='\n            A list of all skill requirements recommended for the\n            sim entering this competition.\n            ', tunable=HorseCompetitionSkillRequirement(description='\n                A single skill requirement for the competition.\n                ', export_class_name='HorseCompetitionSkillRequirement'), export_modes=ExportModes.All), 'horse_skill_requirements': TunableList(description='\n            A list of all skill requirements recommended for the\n            horse entering this competition.\n            ', tunable=HorseCompetitionSkillRequirement(description='\n                A single skill requirement for the competition.\n                ', export_class_name='HorseCompetitionSkillRequirement'), export_modes=ExportModes.All), 'placements': TunableList(description='\n            A list of all the possible placements the competitors can get,\n            in descending order. Should include non-placement.\n            ', tunable=HorseCompetitionPlacement(description='\n                A single placement in the competition.\n                ', export_class_name='HorseCompetitionPlacement'), export_modes=ExportModes.All), 'availability_tests': TunableTestSetWithTooltip(description='\n            The tests that determine if this competition is available.\n            \n            Should include both general availability and competitor\n            specific availability.\n            ', export_modes=(ExportModes.ServerXML,)), 'hero_image': TunableResourceKey(description='\n            The hero image (larger image) used for this\n            competition.\n            ', default=None, resource_types=CompoundTypes.IMAGE, export_modes=ExportModes.All), 'cropped_hero_image': TunableResourceKey(description='\n            A cropped version of the hero image.\n            ', default=None, resource_types=CompoundTypes.IMAGE, export_modes=ExportModes.All), 'icon': TunableResourceKey(description='\n            The icon used to represent this competition.\n            ', default=None, resource_types=CompoundTypes.IMAGE, export_modes=ExportModes.All), 'prerequisite_tests': TunableTestSetWithTooltip(description='\n            The tests to determine if the given participants have\n            met all of the prerequisites, such as completing other competitions.\n            ', export_modes=(ExportModes.ServerXML,)), 'rabbit_hole': TunableReference(description='\n            The rabbit hole that the sim and horse will enter when participating in\n            this competition.\n            ', manager=services.get_instance_manager(sims4.resources.Types.RABBIT_HOLE), class_restrictions=('TwoSimRabbitHole',), export_modes=(ExportModes.ServerXML,))}
(HorseCompetitionReference, HorseCompetitionSnippet) = define_snippet('Horse_Competition', HorseCompetition.TunableFactory())
class HorseCompetitionCategory(HasTunableFactory, AutoFactoryInit):
    FACTORY_TUNABLES = {'name': TunableLocalizedStringFactory(description='\n            The name of this competition category.\n            ', export_modes=ExportModes.All), 'competitions': TunableList(description='\n            Competitions that are in this category.\n            ', tunable=HorseCompetitionReference(description='\n                A competition in this category.\n                '), export_modes=ExportModes.All)}
(HorseCompetitionCategoryReference, HorseCompetitionCategorySnippet) = define_snippet('Horse_Competition_Category', HorseCompetitionCategory.TunableFactory())
@dataclass(frozen=True)
class _ActiveCompetitionInformation:
    __annotations__['competition_id'] = 'int'
    __annotations__['sim_id'] = 'int'
    __annotations__['horse_id'] = 'int'
    rabbit_hole_id = field(compare=False, default=-1)
    __annotations__['rabbit_hole_id'] = 'int'

class HorseCompetitionService(Service):
    COMPETITION_CATEGORIES = TunableList(description='\n        A list of each competition category and its associated data.\n        ', tunable=HorseCompetitionCategoryReference(description='\n            A horse competition category.\n            ', pack_safe=True), export_modes=ExportModes.All)
    NO_COMPETITION_SELECTED_HERO_IMAGE = OptionalTunable(tunable=TunableResourceKey(description='\n            The hero image (larger image) shown when there is no competition\n            selected.\n            ', default=None, resource_types=CompoundTypes.IMAGE, pack_safe=True), export_modes=ExportModes.All)
    MOODS_TOOLTIPS = TunableMapping(description='\n        A mapping between moods and their associated tooltip when\n        the player hovers over an assignee with that mood.\n        ', key_type=TunableReference(description='\n            The mood the assignee that the player hovered over has.\n            ', manager=services.get_instance_manager(sims4.resources.Types.MOOD), pack_safe=True), value_type=TunableLocalizedStringFactory(description='\n            The tooltip to use for the given mood.\n            '), export_modes=(ExportModes.ServerXML,))
    ASSIGNEE_PICKER = UiSkillsSimPicker.TunableFactory(description='\n        The picker dialog to show when selecting Sims to apply this\n        outfit on.\n        ', locked_args={'skills': None, 'include_mood': True, 'should_show_names': False, 'display_filter': False}, export_modes=(ExportModes.ServerXML,))
    HORSE_PICKER_EXCLUSION_TESTS = TunableTestSet(description='\n        Tests used to determine if a given horse will be skipped in the assignee picker.\n        ', export_modes=(ExportModes.ServerXML,))
    SIM_PICKER_EXCLUSION_TESTS = TunableTestSet(description='\n        Tests used to determine if a given sim will be skipped in the assignee picker.\n        ', export_modes=(ExportModes.ServerXML,))
    COMPETITION_START_LOOT_ACTIONS = TunableList(description='\n        A list of loot actions to apply to the sim (actor) and horse (target)\n        that are participating in a competition when the competition starts.\n        ', tunable=TunableReference(description='\n            A loot actions instance to apply to the sim (actor) and horse (target).\n            ', manager=services.get_instance_manager(sims4.resources.Types.ACTION), class_restrictions=('LootActions', 'RandomWeightedLoot'), pack_safe=True), export_modes=(ExportModes.ServerXML,))

    def __init__(self):
        self._active_competitions = set()
        self._competitions_by_id = dict()
        for category in self.COMPETITION_CATEGORIES:
            for competition in category.competitions:
                self._competitions_by_id[competition.guid64] = competition
        self._highest_placements_for_horse = dict()

    @classproperty
    def save_error_code(cls):
        return persistence_error_types.ErrorCodes.SERVICE_SAVE_FAILED_HORSE_COMPETITION_SERVICE

    def save(self, save_slot_data:'SaveGameData'=None, **kwargs):
        competition_proto = GameplaySaveData_pb2.PersistableHorseCompetitionService()
        for competition_information in self._active_competitions:
            with ProtocolBufferRollback(competition_proto.competitions) as entry:
                entry.competition_id = competition_information.competition_id
                entry.rabbit_hole_id = competition_information.rabbit_hole_id
                entry.sim_id = competition_information.sim_id
                entry.horse_id = competition_information.horse_id
        for (horse_id, placements) in self._highest_placements_for_horse.items():
            with ProtocolBufferRollback(competition_proto.horse_placements) as entry:
                entry.horse_id = horse_id
                for (competition_id, placement) in placements.items():
                    with ProtocolBufferRollback(entry.placements) as placement_entry:
                        placement_entry.competition_id = competition_id
                        placement_entry.highest_placement = placement
        save_slot_data.gameplay_data.horse_competition_service = competition_proto

    def load(self, **_):
        save_slot_data = services.get_persistence_service().get_save_slot_proto_buff()
        for entry in save_slot_data.gameplay_data.horse_competition_service.competitions:
            self._register_active_competition(entry.competition_id, entry.rabbit_hole_id, entry.sim_id, entry.horse_id)
        for entry in save_slot_data.gameplay_data.horse_competition_service.horse_placements:
            placement_data = dict()
            for placement_entry in entry.placements:
                placement_data[placement_entry.competition_id] = placement_entry.highest_placement
            self._highest_placements_for_horse[entry.horse_id] = placement_data

    def show_competition_selector_ui(self) -> 'None':
        valid_horses = self._get_all_active_sim_infos_for_species_and_tests(Species.HORSE, self.HORSE_PICKER_EXCLUSION_TESTS)
        valid_sims = self._get_all_active_sim_infos_for_species_and_tests(Species.HUMAN, self.SIM_PICKER_EXCLUSION_TESTS)
        selected_sim = services.active_sim_info()
        if selected_sim not in valid_sims:
            selected_sim = valid_sims[0] if len(valid_sims) > 0 else None
        selected_horse = valid_horses[0] if len(valid_horses) > 0 else None
        op = ShowHorseCompetitionSelector(False, self.COMPETITION_CATEGORIES, self.MOODS_TOOLTIPS, selected_sim, selected_horse)
        distributor.system.Distributor.instance().add_op(services.active_sim_info(), op)

    def pick_new_assignee(self, current_competition_id:'int', current_sim:'Optional[SimInfo]', current_horse:'Optional[SimInfo]', for_horse:'bool') -> 'None':

        def on_assignee_selected(dialog:'UiSimPicker') -> 'None':
            if not dialog.accepted:
                return
            selected_rows = dialog.get_result_tags()
            if selected_rows and (len(selected_rows) <= 0 or selected_rows[0] is None):
                return
            selected_sim = current_sim if for_horse else selected_rows[0]
            selected_horse = current_horse if not for_horse else selected_rows[0]
            op = ShowHorseCompetitionSelector(True, self.COMPETITION_CATEGORIES, self.MOODS_TOOLTIPS, selected_sim, selected_horse)
            distributor.system.Distributor.instance().add_op(services.active_sim_info(), op)

        selected_competition = self.try_get_competition_by_id(current_competition_id)
        if selected_competition is None:
            return
        skill_list = selected_competition.horse_skill_requirements if for_horse else selected_competition.sim_skill_requirements
        skills = [x.skill for x in skill_list]
        dialog = self.ASSIGNEE_PICKER(services.active_sim_info())
        dialog.skills = skills
        dialog.include_mood = for_horse
        if for_horse:
            valid_sim_infos = self._get_all_active_sim_infos_for_species_and_tests(Species.HORSE, self.HORSE_PICKER_EXCLUSION_TESTS)
        else:
            valid_sim_infos = self._get_all_active_sim_infos_for_species_and_tests(Species.HUMAN, self.SIM_PICKER_EXCLUSION_TESTS)
        for sim_info in valid_sim_infos:
            dialog.add_row(SimPickerRow(sim_info.sim_id, tag=sim_info))
        dialog.add_listener(on_assignee_selected)
        dialog.show_dialog()

    def _get_all_active_sim_infos_for_species_and_tests(self, species:'Species', exclusion_tests:'TunableTestSet') -> 'List[SimInfo]':
        valid_sim_infos = []
        for sim_info in services.active_household().sim_info_gen():
            if sim_info.is_instanced():
                if sim_info.species != species:
                    pass
                else:
                    resolver = SingleSimResolver(sim_info)
                    if not len(exclusion_tests) <= 0:
                        if not exclusion_tests.run_tests(resolver):
                            valid_sim_infos.append(sim_info)
                    valid_sim_infos.append(sim_info)
        return valid_sim_infos

    def get_all_competition_ids(self):
        return self._competitions_by_id.keys()

    def try_get_competition_by_id(self, competition_id:'int') -> 'Optional[HorseCompetition]':
        return self._competitions_by_id.get(competition_id, None)

    def try_get_highest_placement(self, horse_id:'int', competition_id:'int') -> 'Optional[int]':
        placements = self._highest_placements_for_horse.get(horse_id)
        if placements is not None:
            local_placement = placements.get(competition_id)
            if local_placement is not None:
                return local_placement
        competition = self.try_get_competition_by_id(competition_id)
        if competition is None:
            return
        placement_traits = [placement.associated_horse_trait for placement in competition.placements]
        horse_sim_info = services.sim_info_manager().get(horse_id)
        for (index, placement_trait) in enumerate(placement_traits):
            if horse_sim_info.has_trait(placement_trait):
                self._try_save_highest_placement_for_horse(competition_id, horse_sim_info, index)
                return index

    def has_medaled(self, horse_id:'int', competition_id:'int') -> 'bool':
        competition = self.try_get_competition_by_id(competition_id)
        if competition is None:
            return False
        placement = self.try_get_highest_placement(horse_id, competition_id)
        return placement is not None and placement < len(competition.placements) - 1

    def _get_unlocked_competitions(self, selected_sim:'SimInfo', selected_horse:'SimInfo') -> 'Set[HorseCompetition]':
        resolver = DoubleSimResolver(selected_sim, selected_horse)
        unlocked_competitions = set()
        for category in self.COMPETITION_CATEGORIES:
            for competition in category.competitions:
                prereq_tests = competition.prerequisite_tests
                if not prereq_tests is None:
                    if prereq_tests.run_tests(resolver):
                        unlocked_competitions.add(competition)
                unlocked_competitions.add(competition)
        return unlocked_competitions

    def _get_weighted_placements(self, competition:'HorseCompetition', selected_sim:'SimInfo', selected_horse:'SimInfo') -> 'List[Tuple[float, HorseCompetitionPlacement]]':
        resolver = DoubleSimResolver(selected_sim, selected_horse)
        weighted_placements = []
        for placement in competition.placements:
            weight = placement.weight.get_multiplier(resolver)
            for skill_multiplier in placement.skill_multipliers:
                weight *= skill_multiplier.get_multiplier(resolver)
            weighted_placements.append((weight, placement))
        return weighted_placements

    def _register_active_competition(self, competition_id:'int', rabbit_hole_id:'int', sim_id:'int', horse_id:'int'):
        competition_info = _ActiveCompetitionInformation(competition_id, sim_id, horse_id, rabbit_hole_id)
        self._active_competitions.add(competition_info)
        self_reference = self

        def on_rabbit_hole_end(canceled):
            self_reference._end_competition(competition_info, canceled)

        services.get_rabbit_hole_service().set_rabbit_hole_expiration_callback(competition_info.sim_id, competition_info.rabbit_hole_id, on_rabbit_hole_end)

    def start_competition(self, competition_id:'int', selected_sim:'SimInfo', selected_horse:'SimInfo') -> 'None':
        selected_competition = self.try_get_competition_by_id(competition_id)
        if selected_competition is None:
            return
        temp_info = _ActiveCompetitionInformation(competition_id, selected_sim.sim_id, selected_horse.sim_id)
        if temp_info in self._active_competitions:
            return
        services.active_household().funds.try_remove_amount(selected_competition.entry_fee, FUNDS_EVENT_COST)
        resolver = DoubleSimResolver(selected_sim, selected_horse)
        for loot_action in self.COMPETITION_START_LOOT_ACTIONS:
            loot_action.apply_to_resolver(resolver)
        rabbit_hole_service = services.get_rabbit_hole_service()
        rabbit_hole_id = rabbit_hole_service.put_sims_in_shared_rabbithole([selected_sim, selected_horse], selected_competition.rabbit_hole)
        if rabbit_hole_id is None:
            return
        self._register_active_competition(competition_id, rabbit_hole_id, selected_sim.sim_id, selected_horse.sim_id)

    def _end_competition(self, competition_info:'_ActiveCompetitionInformation', was_canceled:'bool') -> 'None':
        self._active_competitions.discard(competition_info)
        if competition_info is None or was_canceled:
            return
        selected_competition = self.try_get_competition_by_id(competition_info.competition_id)
        selected_sim = services.sim_info_manager().get(competition_info.sim_id)
        selected_horse = services.sim_info_manager().get(competition_info.horse_id)
        resolver = DoubleSimResolver(selected_sim, selected_horse)
        previously_unlocked_competitions = self._get_unlocked_competitions(selected_sim, selected_horse)
        weighted_placements = self._get_weighted_placements(selected_competition, selected_sim, selected_horse)
        selected_placement_index = weighted_random_index(weighted_placements)
        selected_placement = selected_competition.placements[selected_placement_index]
        self._try_save_highest_placement_for_horse(competition_info.competition_id, selected_horse, selected_placement_index)
        services.active_household().funds.add(selected_placement.simoleon_amount, FUNDS_EVENET_REWARD)
        for loot in selected_placement.loots:
            loot.apply_to_resolver(resolver)
        currently_unlocked_competitions = self._get_unlocked_competitions(selected_sim, selected_horse)
        unlocked_competition = None
        for competition in currently_unlocked_competitions:
            if competition not in previously_unlocked_competitions:
                unlocked_competition = competition
                break
        op = ShowHorseCompetitionResults(selected_sim, selected_horse, selected_competition, selected_placement_index, unlocked_competition)
        distributor.system.Distributor.instance().add_op(services.active_sim_info(), op)

    def _try_save_highest_placement_for_horse(self, competition_id:'int', horse:'SimInfo', selected_placement_index:'int') -> 'None':
        if horse.sim_id not in self._highest_placements_for_horse:
            self._highest_placements_for_horse[horse.sim_id] = dict()
        highest_placements = self._highest_placements_for_horse[horse.sim_id]
        highest_placement = highest_placements.get(competition_id)
        if highest_placement is None or selected_placement_index < highest_placement:
            highest_placements[competition_id] = selected_placement_index
