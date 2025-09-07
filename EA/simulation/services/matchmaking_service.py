from __future__ import annotationsimport telemetry_helperfrom sims4 import protocol_buffer_utilsfrom typing import TYPE_CHECKINGif TYPE_CHECKING:
    from typing import *
    from sims.sim_info import SimInfo
    from traits.preference import Preference
    from traits.traits import Trait
    from protocolbuffers import FileSerialization_pb2 as serializationimport mathimport mtximport protocolbuffersimport randomimport servicesimport sims4.logfrom cas.cas import generate_random_siminfofrom date_and_time import DATE_AND_TIME_ZEROfrom distributor.rollback import ProtocolBufferRollbackfrom distributor.ops import ShowMatchmakingDialogfrom distributor.system import Distributorfrom event_testing.test_events import TestEventfrom filters.tunable import TunableSimFilter, FilterTermVariant, AgeFilterTerm, GenderFilterTerm, GallerySimFilterTerm, TraitBlacklistFilterTermfrom interactions.utils.tunable_icon import TunableIconAllPacksfrom matchmaking.matchmaking_enum import ProfileTypefrom matchmaking.matchmaking_profiles import MatchmakingData, MatchmakingProfilefrom persistence_error_types import ErrorCodesfrom protocolbuffers import Sims_pb2from protocolbuffers.GameplaySaveData_pb2 import GameplayOptionsfrom protocolbuffers.ResourceKey_pb2 import ResourceKeyfrom relationships.global_relationship_tuning import RelationshipGlobalTuningfrom relationships.relationship_track import RelationshipTrackfrom sims.global_gender_preference_tuning import GenderPreferenceType, GlobalGenderPreferenceTuning, ExploringOptionsStatusfrom sims.household_enums import HouseholdChangeOriginfrom sims.household_manager import HouseholdFixupHelperfrom sims.sim_info_base_wrapper import SimInfoBaseWrapperfrom sims.sim_info_types import Age, Gender, Speciesfrom sims.sim_spawner import SimSpawner, SimCreatorfrom sims4.common import Packfrom sims4.service_manager import Servicefrom sims4.tuning.tunable import Tunable, TunableEnumEntry, TunableEnumSet, TunableMapping, TunableRange, TunableReference, TunablePackSafeReference, TunableList, TunableTuplefrom sims4.protocol_buffer_utils import has_fieldfrom sims4.utils import classpropertyfrom traits.trait_type import TraitTypefrom tunable_time import TunableTimeSpanfrom ui.ui_dialog_notification import TunableUiDialogNotificationSnippetlogger = sims4.log.Logger('Matchmaking', default_owner='sucywang')TELEMETRY_GROUP_MATCHMAKING = 'MAMK'TELEMETRY_HOOK_REFRESH = 'RFSH'TELEMETRY_FIELD_REFRESH_ACTION = 'rfsh'writer = sims4.telemetry.TelemetryWriter(TELEMETRY_GROUP_MATCHMAKING)NUM_NPCS_FROM_GALLERY = 1NUM_TRAITS_TO_DISPLAY = 2ON_CONTACT_NPC_REL_GAIN = 10MAX_POSE_INDEX = 8SIM_INFO_CAP = 600
class MatchmakingService(Service):
    NUM_NPCS_TO_GENERATE = TunableRange(description='\n        The number of NPC profiles that will be made to populate the app. The profiles will refresh daily.\n        ', tunable_type=int, default=5, minimum=0, maximum=15)
    NUM_NPCS_FROM_WORLD = TunableRange(description='\n        The number of NPCs that will be pulled from the world to populate the app. The profiles will refresh daily.\n        ', tunable_type=int, default=1, minimum=0, maximum=5)
    REPLACE_GALLERY_NPC = Tunable(description='\n        If set to true, replace the number of gallery NPCs with the same number of \n        generated NPCs on connection failure.\n        ', tunable_type=bool, default=True)
    ATTRACTED_TO_GENDER_AND_TRAIT_MAPPING = TunableMapping(description='\n        A mapping of a gender to its associated "attracted to" gender preference trait.\n         ', key_name='Gender', key_type=TunableEnumEntry(description='\n            A gender enum.\n            ', tunable_type=Gender, default=Gender.MALE), value_name='Gender preference trait', value_type=TunableReference(description='\n            The associated "attracted to gender" preference trait.\n            ', manager=services.get_instance_manager(sims4.resources.Types.TRAIT)), minlength=2)
    GENERATED_NPC_TRAIT_TYPE_ALLOWED = TunableEnumSet(description='\n        The list of trait types that generated NPCs are allowed to have.\n        When making new NPCs, we cannot do filter term tests due to base sim infos not\n        having a trait tracker. To make sure the NPCs does not have any special behavior, only the\n        traits in this list are kept while the rest will be cleared.\n        ', enum_type=TraitType, enum_default=TraitType.PERSONALITY, minlength=1)
    NPC_PROFILE_FILTER = TunablePackSafeReference(description='\n        A filter used for picking NPCs from the world to populate matchmaking UI. \n        We check NPCs against this filter to make sure they are\n        a dateable candidate.\n        ', manager=services.get_instance_manager(sims4.resources.Types.SIM_FILTER), class_restrictions=('TunableSimFilter',))
    NO_OCCULT_FILTER_TERM = FilterTermVariant(description='\n        A filter terms that is used to filter out occult sims when players have the "Enable Occult Sims" pack setting\n        disabled.\n        ')
    NPC_COOLDOWN = TunableTimeSpan(description='\n        The amount of time in sim time before an existing NPC could show up in the app as a candidate again.\n        ', default_days=2)
    REFRESH_BUTTON_COOLDOWN = TunableTimeSpan(description="\n        The interval in sim time between interactions with the 'show more' button.\n        ", default_days=2)
    DAILY_CONTACT_ACTIONS_LIMIT = TunableRange(description='\n        How many times in a sim day a sim can contact a candidate through the app.\n        ', tunable_type=int, default=1, minimum=1, maximum=3)
    MAXIMUM_SAVE_LIMIT = TunableRange(description='\n        The maximum number of candidate profiles a sim could save.\n        ', tunable_type=int, default=10, minimum=1, maximum=15)
    ASK_ON_DATE_AFFORDANCE = TunablePackSafeReference(description='\n        The affordance to start create a date UI between two Sims.\n        ', manager=services.get_instance_manager(sims4.resources.Types.INTERACTION))
    OPEN_SELFIE_CAMERA_AFFORDANCE = TunableReference(description='\n        The affordance to start the camera in portrait selfie mode.\n        ', manager=services.get_instance_manager(sims4.resources.Types.INTERACTION), class_restrictions='SuperInteraction', pack_safe=True)
    GALLERY_MINIMUM_DOWNLOAD_COUNT = TunableRange(description='\n        The minimum download count the server will use to select gallery contents for the matchmaking app.\n        \n        A value of 0 means the download count will not be considered.\n        ', tunable_type=int, default=0, minimum=0)
    GALLERY_UPLOAD_TIME_RANGE_START = TunableRange(description='\n        The lower bound upload time the server will use to select gallery contents for the matchmaking app.\n        \n        A value of 0 means the upload time is current time.\n        ', tunable_type=int, default=0, minimum=0)
    GALLERY_UPLOAD_TIME_RANGE_END = TunableRange(description='\n        The upper bound upload time the server will use to select gallery contents for the matchmaking app.\n        \n        A value of 0 means the upload time is current time.\n        ', tunable_type=int, default=0, minimum=0)
    SET_TRAITS_AFFORDANCE = TunablePackSafeReference(description='\n        The affordance to set current Sim profile traits.\n        ', manager=services.get_instance_manager(sims4.resources.Types.INTERACTION))
    PROFILE_BACKGROUND_IMAGES = TunableList(description='\n        A list of background images that will be assigned to generated Matchmaking profiles\n        that will be shown in the Candidates/Saved tabs when viewing Matchmaking app profiles.\n        ', tunable=TunableIconAllPacks(description='\n            The image for a specific profile background to assign to a generated profile in\n            the Matchmaking app which will be displayed in Candidates/Saved tabs.\n            ', allow_none=False))
    PHOTO_POSE_INDEX_WEIGHTS = TunableList(description='\n        A list of photo pose indexes to a weighted chance that pose index would be chosen for \n        the profile photos of the sims on the matchmaking app.\n        ', tunable=TunableTuple(pose_index=TunableRange(description='\n                The pose index that mirrors MatchmakingPoses under Client_ThumbnailPoses tuning.\n                (The index max is set to 8, if new poses are added, please contact a GPE to adjust this\n                max.)\n                ', tunable_type=int, default=0, minimum=0, maximum=8), weight=TunableRange(description='\n                The weighted chance that this pose index will be selected to generate a profile photo.\n                ', tunable_type=float, default=0.1, minimum=0, maximum=1)))
    UNIQUE_PHOTO_POSE_INDEXES = TunableList(description='\n        The list of photo pose indexes that has to be unique when generating candidate photos.\n        (The max allowed index is 8, to match with client tuning. If this needs to be changed, \n        please contact your GPE partner.)\n        ', tunable=TunableRange(description='\n            The pose index.\n            ', tunable_type=int, default=2, minimum=0, maximum=8))
    GENERATE_HOUSEHOLD_MEMBERS_CHANCE = TunableRange(description='\n        Weighted chance that a generated NPC will come from the list of random household templates.\n        ', tunable_type=float, default=0.1, minimum=0.0)
    RANDOM_HOUSEHOLD_TEMPLATES = TunableList(description='\n        A list of Household Templates and their weighted chance that a generated NPC could come from.\n        ', tunable=TunableTuple(description='\n            Weights of the household templates.\n            ', household_template=TunableReference(description='\n                Individual Household Templates to randomly pick from for a generated NPC.\n                If a template is selected, the first household member will be picked as the NPC that will \n                appear on the app.\n                ', manager=services.get_instance_manager(sims4.resources.Types.SIM_TEMPLATE), class_restrictions='HouseholdTemplate', pack_safe=True), weight=TunableRange(description='\n                Weighted chance the generated NPC will be from this household.\n                ', tunable_type=float, default=0.1, minimum=0.0)))
    EVENTS = (TestEvent.SimDeathTypeSet,)

    def __init__(self):
        self.actor_id_to_matchmaking_data = {}
        self.candidate_id_to_matchmaking_profile = {}
        self.candidate_id_to_household_templates = {}
        self._gallery_sims_enabled = True
        self._occult_sims_enabled = True
        self._gallery_sims_favorites_only_enabled = False
        self._gallery_sims_trait_exclusions = []
        self.gallery_kill_switch_enabled = False
        self.actor_id_to_pose_indexes = {}
        self.real_id_to_generated_id = {}
        self.remote_id_to_sim_id = {}
        self.current_actor_sim_info = None

    def start(self) -> 'None':
        for npc_profile_filter in self.NPC_PROFILE_FILTER.get_filter_terms():
            if isinstance(npc_profile_filter, TraitBlacklistFilterTerm):
                for trait in npc_profile_filter.traits:
                    self._gallery_sims_trait_exclusions.append(trait.guid64)
        services.get_event_manager().register(self, self.EVENTS)

    def stop(self) -> 'None':
        services.get_event_manager().unregister(self, self.EVENTS)

    @classproperty
    def required_packs(cls) -> 'Tuple[Pack]':
        return (Pack.EP16,)

    @classproperty
    def save_error_code(cls) -> 'ErrorCodes':
        return ErrorCodes.SERVICE_SAVE_FAILED_MATCHMAKING_SERVICE

    def save_options(self, options_proto:'GameplayOptions') -> 'None':
        options_proto.matchmaking_gallery_sims_enabled = self._gallery_sims_enabled
        options_proto.matchmaking_occult_sims_enabled = self._occult_sims_enabled
        options_proto.matchmaking_gallery_sims_favorites_only_enabled = self._gallery_sims_favorites_only_enabled

    def load_options(self, options_proto:'GameplayOptions') -> 'None':
        self._gallery_sims_enabled = options_proto.matchmaking_gallery_sims_enabled
        self._occult_sims_enabled = options_proto.matchmaking_occult_sims_enabled
        self._gallery_sims_favorites_only_enabled = options_proto.matchmaking_gallery_sims_favorites_only_enabled

    def set_gallery_kill_switch(self, enabled:'bool'):
        self.gallery_kill_switch_enabled = enabled

    def handle_event(self, sim_info, event, resolver=None):
        if event == TestEvent.PhotoTaken:
            self.unregister_photo_taken_event()
            if sim_info is not self.current_actor_sim_info:
                return
            matchmaking_data = self.actor_id_to_matchmaking_data[self.current_actor_sim_info.sim_id]
            if matchmaking_data is not None:
                photo_object = resolver.event_kwargs.get('photo_object')
                res_key = resolver.event_kwargs.get('res_key')
                if photo_object is not None and res_key is not None:
                    sim = self.current_actor_sim_info.get_sim_instance()
                    if sim is not None:
                        sim.inventory_component.try_move_object_to_hidden_inventory(photo_object, compact=False)
                    matchmaking_data.selfie_res_key = res_key
                    self.show_matchmaking_dialog(self.current_actor_sim_info.sim_id)
        elif event == TestEvent.ExitedPhotoMode:
            self.unregister_photo_mode_exited_event()
            if sim_info is None and self.current_actor_sim_info is None:
                return
            self.show_matchmaking_dialog(self.current_actor_sim_info.sim_id)
        elif event == TestEvent.SimDeathTypeSet:
            sim_id = sim_info.sim_id
            if sim_id in self.candidate_id_to_matchmaking_profile:
                del self.candidate_id_to_matchmaking_profile[sim_id]
            elif sim_id in self.real_id_to_generated_id:
                profile_id = self.real_id_to_generated_id[sim_id]
                if profile_id in self.actor_id_to_matchmaking_data:
                    del self.actor_id_to_matchmaking_data[profile_id]
                if profile_id in self.candidate_id_to_matchmaking_profile:
                    del self.candidate_id_to_matchmaking_profile[profile_id]

    def register_photo_taken_event(self, actor_sim_info):
        self.current_actor_sim_info = actor_sim_info
        services.get_event_manager().register_single_event(self, TestEvent.PhotoTaken)

    def unregister_photo_taken_event(self):
        services.get_event_manager().unregister_single_event(self, TestEvent.PhotoTaken)

    def register_photo_mode_exited_event(self, actor_sim_info):
        self.current_actor_sim_info = actor_sim_info
        services.get_event_manager().register_single_event(self, TestEvent.ExitedPhotoMode)

    def unregister_photo_mode_exited_event(self):
        services.get_event_manager().unregister_single_event(self, TestEvent.ExitedPhotoMode)

    @property
    def gallery_sims_enabled(self) -> 'bool':
        return self._gallery_sims_enabled

    @gallery_sims_enabled.setter
    def gallery_sims_enabled(self, enabled:'bool') -> 'None':
        self._gallery_sims_enabled = enabled

    @property
    def gallery_sims_favorites_only_enabled(self) -> 'bool':
        return self._gallery_sims_favorites_only_enabled

    @gallery_sims_favorites_only_enabled.setter
    def gallery_sims_favorites_only_enabled(self, enabled:'bool') -> 'None':
        self._gallery_sims_favorites_only_enabled = enabled

    @property
    def gallery_sims_trait_exclusions(self) -> 'List':
        return self._gallery_sims_trait_exclusions

    @property
    def occult_sims_enabled(self) -> 'bool':
        return self._occult_sims_enabled

    @occult_sims_enabled.setter
    def occult_sims_enabled(self, enabled:'bool') -> 'None':
        self._occult_sims_enabled = enabled

    @staticmethod
    def get_displayed_trait_ids(trait_list:'List[int]'):
        displayed_trait_ids = []
        trait_manager = services.get_instance_manager(sims4.resources.Types.TRAIT)
        for trait_id in trait_list:
            trait = trait_manager.get(trait_id)
            if trait is None:
                pass
            elif not trait.is_personality_trait:
                pass
            elif len(displayed_trait_ids) < NUM_TRAITS_TO_DISPLAY:
                displayed_trait_ids.append(trait_id)
        return displayed_trait_ids

    def clear_pose_indexes_for_actor(self, actor_id):
        if actor_id in self.actor_id_to_pose_indexes:
            self.actor_id_to_pose_indexes[actor_id].clear()
        else:
            self.actor_id_to_pose_indexes[actor_id] = []

    def create_matchmaking_profile_from_sim_info(self, candidate_info:'Union[SimInfoBaseWrapper, SimInfo]', profile_type:'ProfileType') -> 'MatchmakingProfile':
        first_name = candidate_info.first_name
        age = candidate_info.age
        gender = candidate_info.gender
        displayed_trait_ids = self.get_displayed_trait_ids(candidate_info.trait_ids)
        profile = MatchmakingProfile(candidate_info.sim_id, profile_type, first_name, age, gender, displayed_trait_ids)
        profile.sim_info = candidate_info
        if profile_type == ProfileType.WORLD_NPC:
            profile.real_sim_id = profile.sim_info.sim_id
        return profile

    def get_unique_pose_index_for_actor(self, actor_id) -> 'int':
        taken_poses = list(set(self.actor_id_to_pose_indexes[actor_id]) & set(self.UNIQUE_PHOTO_POSE_INDEXES))
        available_poses_and_weights = [(pose, weight) for (pose, weight) in self.PHOTO_POSE_INDEX_WEIGHTS if pose[1] not in taken_poses]
        pose_list = [pose[1] for (pose, weight) in available_poses_and_weights]
        weight_list = [weight[1] for (pose, weight) in available_poses_and_weights]
        return random.choices(pose_list, weight_list).pop()

    def add_gallery_sim(self, gallery_sim_profile:'MatchmakingProfile') -> 'None':
        if len(self.PROFILE_BACKGROUND_IMAGES) > 0:
            proto_bg_res_key = protocolbuffers.ResourceKey_pb2.ResourceKey()
            bg_res_key = random.choice(self.PROFILE_BACKGROUND_IMAGES)
            proto_bg_res_key.type = bg_res_key.type
            proto_bg_res_key.group = bg_res_key.group
            proto_bg_res_key.instance = bg_res_key.instance
            gallery_sim_profile.profile_bg_res_key = proto_bg_res_key
        self.candidate_id_to_matchmaking_profile[gallery_sim_profile.sim_id] = gallery_sim_profile

    def select_age(self, actor_id:'int', age:'Age') -> 'None':
        matchmaking_data = self.actor_id_to_matchmaking_data[actor_id]
        if not matchmaking_data:
            logger.error('Valid matchmaking data not found for sim {}.', actor_id)
            return
        matchmaking_data.selected_ages.add(age)

    def deselect_age(self, actor_id:'int', age:'Age') -> 'None':
        matchmaking_data = self.actor_id_to_matchmaking_data[actor_id]
        if not matchmaking_data:
            logger.error('Valid matchmaking data not found for sim {}.', actor_id)
            return
        if age in matchmaking_data.selected_ages:
            matchmaking_data.selected_ages.remove(age)

    def create_npc_info(self, actor_info:'SimInfo', age:'Age', gender:'Gender') -> 'SimInfo':
        npc_info = SimInfoBaseWrapper(age=age, gender=gender, species=Species.HUMAN)
        generate_random_siminfo(npc_info._base)
        trait_manager = services.get_instance_manager(sims4.resources.Types.TRAIT)
        npc_traits = []
        num_personality_traits = 0
        npc_trait_ids = npc_info.trait_ids
        for trait_id in npc_trait_ids:
            trait = trait_manager.get(trait_id)
            if trait is None:
                pass
            elif trait.trait_type in self.GENERATED_NPC_TRAIT_TYPE_ALLOWED:
                npc_traits.append(trait)
                if trait.is_personality_trait:
                    num_personality_traits += 1
        if num_personality_traits < NUM_TRAITS_TO_DISPLAY:
            available_traits = [trait for trait in trait_manager.types.values() if trait.is_personality_trait and trait not in npc_traits]
            while num_personality_traits < NUM_TRAITS_TO_DISPLAY and len(available_traits > 0):
                trait = random.choice(available_traits)
                available_traits.remove(trait)
                npc_traits.append(trait)
                num_personality_traits += 1
        gender_preference_traits_to_add = []
        gender_preference_traits_to_add.append(self.ATTRACTED_TO_GENDER_AND_TRAIT_MAPPING[Gender.FEMALE])
        gender_preference_traits_to_add.append(self.ATTRACTED_TO_GENDER_AND_TRAIT_MAPPING[Gender.MALE])
        gender_preference_traits_to_add.append(GlobalGenderPreferenceTuning.EXPLORING_SEXUALITY_TRAITS_MAPPING.get(ExploringOptionsStatus.EXPLORING))
        for trait in gender_preference_traits_to_add:
            if trait not in npc_traits:
                npc_traits.append(trait)
        npc_info.set_trait_ids_on_base(trait_ids_override=list(t.guid64 for t in npc_traits))
        npc_info.first_name = SimSpawner.get_random_first_name(gender, Species.HUMAN)
        npc_info.manager = services.sim_info_manager()
        Distributor.instance().add_object(npc_info)
        return npc_info

    def refresh_npcs_for_sim(self, actor_info:'SimInfo', replace_gallery_sims:'bool'=False, gallery_ids:'Optional[List[int]]'=None) -> 'None':
        actor_id = actor_info.sim_id
        if actor_id not in self.actor_id_to_matchmaking_data:
            logger.error('Valid matchmaking data not found for sim {}.', actor_id)
            return
        matchmaking_data = self.actor_id_to_matchmaking_data[actor_id]
        last_refresh = matchmaking_data.get_last_time_refreshed()
        if last_refresh is not DATE_AND_TIME_ZERO and matchmaking_data.is_first_refresh():
            matchmaking_data.update_first_refresh()
        self.clear_pose_indexes_for_actor(actor_id)
        if not matchmaking_data.selected_ages:
            matchmaking_data.selected_ages = {Age.YOUNGADULT, Age.ADULT, Age.ELDER}
        age_options = list(matchmaking_data.selected_ages)
        gender_options = set()
        attracted_options = actor_info.get_attracted_genders(GenderPreferenceType.ROMANTIC)
        woohoo_options = actor_info.get_attracted_genders(GenderPreferenceType.WOOHOO)
        if attracted_options or not woohoo_options:
            gender_options = {Gender.MALE, Gender.FEMALE}
        else:
            gender_options = attracted_options.union(woohoo_options)
        npc_infos_to_show = []
        npcs_on_cooldown = matchmaking_data.npcs_on_cooldown
        gallery_sims_on_cooldown = matchmaking_data.gallery_sims_on_cooldown
        all_sims_on_cooldown = gallery_sims_on_cooldown
        current_time = services.time_service().sim_now
        for (sim_id, time) in all_sims_on_cooldown.items():
            if current_time - time > self.NPC_COOLDOWN:
                if sim_id in npcs_on_cooldown:
                    del npcs_on_cooldown[sim_id]
                elif sim_id in gallery_sims_on_cooldown:
                    del gallery_sims_on_cooldown[sim_id]
        for sim_id in matchmaking_data.candidate_ids:
            if sim_id in self.candidate_id_to_matchmaking_profile:
                profile = self.candidate_id_to_matchmaking_profile[sim_id]
                if profile.profile_type == ProfileType.WORLD_NPC:
                    npcs_on_cooldown[sim_id] = current_time
                elif profile.profile_type == ProfileType.GALLERY_NPC and sim_id in self.candidate_id_to_matchmaking_profile:
                    matchmaking_profile = self.candidate_id_to_matchmaking_profile[sim_id]
                    gallery_sims_on_cooldown[matchmaking_profile.exchange_data_remote_id] = current_time
        for sim_id in matchmaking_data.candidate_ids:
            if sim_id not in matchmaking_data.saved_candidate_ids and sim_id in self.candidate_id_to_matchmaking_profile:
                del self.candidate_id_to_matchmaking_profile[sim_id]
        matchmaking_data.clear_candidates()
        additional_filter_terms = []
        age_options.sort()
        age_filter_term = AgeFilterTerm(min_value=age_options[0], max_value=age_options[-1], ideal_value=random.choice(age_options), invert_score=False, minimum_filter_score=0)
        additional_filter_terms.append(age_filter_term)
        gallery_filter_term = GallerySimFilterTerm(invert_score=True, minimum_filter_score=1)
        additional_filter_terms.append(gallery_filter_term)
        if 0 < len(gender_options) and len(gender_options) < 2:
            gender_filter_term = GenderFilterTerm(gender=list(gender_options)[0], minimum_filter_score=0)
            additional_filter_terms.append(gender_filter_term)
        if not self._occult_sims_enabled:
            additional_filter_terms.append(self.NO_OCCULT_FILTER_TERM)
        sim_ids_on_cooldown = set(npcs_on_cooldown.keys()).union(matchmaking_data.saved_candidate_ids)
        num_of_sims_to_find = self.NUM_NPCS_FROM_WORLD
        num_generated_npcs_needed = self.NUM_NPCS_TO_GENERATE + NUM_NPCS_FROM_GALLERY if replace_gallery_sims or self.gallery_kill_switch_enabled or not self._gallery_sims_enabled else self.NUM_NPCS_TO_GENERATE
        sim_info_manager = services.sim_info_manager()
        sim_info_count = len(sim_info_manager)
        if sim_info_count > SIM_INFO_CAP:
            num_of_sims_to_find = self.NUM_NPCS_FROM_WORLD + self.NUM_NPCS_TO_GENERATE
            num_generated_npcs_needed = 0
        existing_npcs = services.sim_filter_service().submit_matching_filter(number_of_sims_to_find=num_of_sims_to_find, requesting_sim_info=actor_info, sim_filter=self.NPC_PROFILE_FILTER, allow_instanced_sims=True, allow_yielding=False, blacklist_sim_ids=sim_ids_on_cooldown, additional_filter_terms=tuple(additional_filter_terms))
        for npc in existing_npcs:
            npc_infos_to_show.append((npc.sim_info, ProfileType.WORLD_NPC))
        num_generated_npcs_needed += num_of_sims_to_find - len(existing_npcs)
        while num_generated_npcs_needed > 0:
            random_age = random.choice(age_options)
            random_gender = random.choice(list(gender_options))
            chosen_template = None
            if random.random() <= self.GENERATE_HOUSEHOLD_MEMBERS_CHANCE:
                matching_templates = []
                weights = []
                for weighted_household_template in self.RANDOM_HOUSEHOLD_TEMPLATES:
                    sim_template = weighted_household_template.household_template.get_household_member_templates()[0]
                    if sim_template is not None and sim_template.matches_creation_data(age_min=random_age, species=Species.HUMAN):
                        sim_template.sim_creator.gender = random_gender
                        matching_templates.append(weighted_household_template.household_template)
                        weights.append(weighted_household_template.weight)
                if weights:
                    chosen_template = random.choices(matching_templates, weights)[0]
            npc_info = self.create_npc_info(actor_info, random_age, random_gender)
            if chosen_template is not None:
                self.candidate_id_to_household_templates[npc_info.sim_id] = chosen_template
            npc_infos_to_show.append((npc_info, ProfileType.GENERATED_NPC))
            num_generated_npcs_needed -= 1
        attraction_preferences = set(filter(lambda trait: trait.is_attraction_trait, actor_info.trait_tracker))
        trait_manager = services.get_instance_manager(sims4.resources.Types.TRAIT)
        for (npc_info, profile_type) in npc_infos_to_show:
            npc_id = npc_info.sim_id
            matchmaking_data.add_candidate(npc_id)
            new_profile = self.create_matchmaking_profile_from_sim_info(npc_info, profile_type)
            if profile_type == ProfileType.WORLD_NPC:
                zone_id = npc_info.household.home_zone_id
                persistence_service = services.get_persistence_service()
                if persistence_service is not None:
                    neighborhood_proto = persistence_service.get_neighborhood_proto_buf_from_zone_id(zone_id)
                    if neighborhood_proto is not None:
                        new_profile.region_name = neighborhood_proto.name
            if len(self.PROFILE_BACKGROUND_IMAGES) > 0:
                proto_bg_res_key = protocolbuffers.ResourceKey_pb2.ResourceKey()
                bg_res_key = random.choice(self.PROFILE_BACKGROUND_IMAGES)
                proto_bg_res_key.type = bg_res_key.type
                proto_bg_res_key.group = bg_res_key.group
                proto_bg_res_key.instance = bg_res_key.instance
                new_profile.profile_bg_res_key = proto_bg_res_key
            for preference in attraction_preferences:
                for trait_id in new_profile.displayed_traits_map:
                    new_profile.displayed_traits_map[trait_id] += int(self.calculate_preference_score_for_trait(preference, trait_manager.get(trait_id)))
            self.candidate_id_to_matchmaking_profile[npc_id] = new_profile
            if new_profile.sim_id in self.candidate_id_to_household_templates:
                new_profile.is_from_template = True
            new_profile.pose_index = self.get_unique_pose_index_for_actor(actor_id)
            self.actor_id_to_pose_indexes[actor_id].append(new_profile.pose_index)
        current_time = services.time_service().sim_now
        matchmaking_data.update_last_time_refreshed(current_time)
        if gallery_ids is not None:
            for npc_id in gallery_ids:
                matchmaking_data.add_candidate(npc_id)
        with telemetry_helper.begin_hook(writer, TELEMETRY_HOOK_REFRESH, sim_info=actor_info) as hook:
            hook.write_bool(TELEMETRY_FIELD_REFRESH_ACTION, True)
        self.show_matchmaking_dialog(actor_id, True)

    @staticmethod
    def calculate_preference_score_for_trait(preference:'Preference', trait:'Trait') -> 'int':
        preference_item = preference.preference_item
        if preference_item is None:
            return 0
        trait_map = preference_item.trait_map
        if not trait_map:
            return 0
        else:
            multiplier = 1 if preference_item.like == preference else -1
            if trait in trait_map:
                return trait_map[trait]*multiplier
        return 0

    def get_valid_npc_ids_from_list(self, candidate_id_list:'List[int]') -> 'List[int]':
        valid_ids = set()
        trait_manager = services.get_instance_manager(sims4.resources.Types.TRAIT)
        sim_info_manager = services.sim_info_manager()
        for npc_id in candidate_id_list:
            if npc_id in self.candidate_id_to_matchmaking_profile:
                npc_profile = self.candidate_id_to_matchmaking_profile[npc_id]
                profile_type = npc_profile.profile_type
                npc_info = npc_profile.sim_info
                if npc_info is not None:
                    if npc_info.is_ghost:
                        pass
                    else:
                        traits_valid = True
                        for trait_id in npc_info.trait_ids:
                            trait = trait_manager.get(trait_id)
                            if trait is None:
                                traits_valid = False
                            elif trait.entitlement is not None and not mtx.has_entitlement(trait.entitlement):
                                traits_valid = False
                        if not traits_valid:
                            pass
                        elif not (profile_type == ProfileType.GALLERY_NPC and self.gallery_kill_switch_enabled):
                            if not self.gallery_sims_enabled:
                                pass
                            elif profile_type == ProfileType.WORLD_NPC and sim_info_manager.get(npc_id) is None:
                                pass
                            else:
                                valid_ids.add(npc_id)
                            valid_ids.add(npc_id)
                if not (profile_type == ProfileType.GALLERY_NPC and self.gallery_kill_switch_enabled):
                    if not self.gallery_sims_enabled:
                        pass
                    elif profile_type == ProfileType.WORLD_NPC and sim_info_manager.get(npc_id) is None:
                        pass
                    else:
                        valid_ids.add(npc_id)
                    valid_ids.add(npc_id)
        return valid_ids

    def check_relationship(self, actor_info:'SimInfo', list_profiles:'List[MatchmakingProfile]') -> 'None':
        if actor_info is None:
            return
        for profile in list_profiles:
            if profile.contacted is False:
                if profile.profile_type == ProfileType.GALLERY_NPC:
                    if actor_info.relationship_tracker.has_relationship(self.remote_id_to_sim_id[profile.exchange_data_remote_id]):
                        profile.contacted = True
                        if actor_info.relationship_tracker.has_relationship(profile.sim_id):
                            profile.contacted = True
                elif actor_info.relationship_tracker.has_relationship(profile.sim_id):
                    profile.contacted = True

    def check_hidden_relationship(self, actor_info:'SimInfo', list_profiles:'List[MatchmakingProfile]') -> 'None':
        if actor_info is None:
            return
        for profile in list_profiles:
            if profile.profile_type == ProfileType.GALLERY_NPC and (profile.exchange_data_remote_id in self.remote_id_to_sim_id.keys() and actor_info.relationship_tracker.has_relationship(self.remote_id_to_sim_id[profile.exchange_data_remote_id])) and actor_info.relationship_tracker.is_hidden(self.remote_id_to_sim_id[profile.exchange_data_remote_id]):
                profile.rel_is_hidden = True
            elif profile.profile_type == ProfileType.GENERATED_NPC and (profile.contacted and actor_info.relationship_tracker.has_relationship(profile.real_sim_id)) and actor_info.relationship_tracker.is_hidden(profile.real_sim_id):
                profile.rel_is_hidden = True
            elif actor_info.relationship_tracker.has_relationship(profile.sim_id) and actor_info.relationship_tracker.is_hidden(profile.sim_id):
                profile.rel_is_hidden = True
            else:
                profile.rel_is_hidden = False

    def unhide_hidden_relationship(self, actor_info:'SimInfo', profile:'MatchmakingProfile') -> 'None':
        if profile.profile_type == ProfileType.GALLERY_NPC and profile.exchange_data_remote_id in self.remote_id_to_sim_id.keys() and actor_info.relationship_tracker.is_hidden(self.remote_id_to_sim_id[profile.exchange_data_remote_id]):
            actor_info.relationship_tracker.hide_relationship(self.remote_id_to_sim_id[profile.exchange_data_remote_id], False)
        elif profile.profile_type == ProfileType.GENERATED_NPC and profile.contacted and actor_info.relationship_tracker.is_hidden(profile.real_sim_id):
            actor_info.relationship_tracker.hide_relationship(profile.real_sim_id, False)
        elif actor_info.relationship_tracker.is_hidden(profile.sim_id):
            actor_info.relationship_tracker.hide_relationship(profile.sim_id, False)

    def show_matchmaking_dialog(self, actor_id:'int', is_update:'bool'=False, is_traits_display_update:'bool'=False) -> 'None':
        actor_info = services.sim_info_manager().get(actor_id)
        if actor_info is None or actor_info.is_npc:
            logger.error('Not a Valid SimID or Sim is an NPC.')
            return
        list_matchmaking_profiles = []
        current_time = services.time_service().sim_now
        if actor_id not in self.actor_id_to_matchmaking_data:
            matchmaking_data = MatchmakingData(actor_id, self.DAILY_CONTACT_ACTIONS_LIMIT)
            if len(self.PROFILE_BACKGROUND_IMAGES) > 0:
                proto_actor_bg_res_key = protocolbuffers.ResourceKey_pb2.ResourceKey()
                actor_bg_res_key = random.choice(self.PROFILE_BACKGROUND_IMAGES)
                proto_actor_bg_res_key.type = actor_bg_res_key.type
                proto_actor_bg_res_key.group = actor_bg_res_key.group
                proto_actor_bg_res_key.instance = actor_bg_res_key.instance
                matchmaking_data.bg_res_key = proto_actor_bg_res_key
            self.actor_id_to_matchmaking_data[actor_id] = matchmaking_data
        else:
            matchmaking_data = self.actor_id_to_matchmaking_data[actor_id]
            valid_candidate_ids = self.get_valid_npc_ids_from_list(matchmaking_data.candidate_ids)
            list_matchmaking_profiles = [self.candidate_id_to_matchmaking_profile[sim_id] for sim_id in valid_candidate_ids]
            last_reset = matchmaking_data.get_time_num_contact_action_reset()
            if math.floor(current_time.absolute_days()) > math.floor(last_reset.absolute_days()):
                matchmaking_data.reset_num_contact_actions(self.DAILY_CONTACT_ACTIONS_LIMIT, current_time)
        traits_selected = matchmaking_data.selected_trait_ids
        player_sim_profile_trait_ids = [trait.guid64 for trait in actor_info.trait_tracker.personality_traits + actor_info.trait_tracker.aspiration_traits]
        for trait_id in player_sim_profile_trait_ids:
            if len(traits_selected) < NUM_TRAITS_TO_DISPLAY:
                traits_selected.add(trait_id)
            else:
                break
        matchmaking_data.select_traits(traits_selected)
        valid_saved_ids = self.get_valid_npc_ids_from_list(matchmaking_data.saved_candidate_ids)
        saved_profiles = [self.candidate_id_to_matchmaking_profile[sim_id] for sim_id in valid_saved_ids]
        last_refresh = matchmaking_data.get_last_time_refreshed()
        cooldown_time_left_in_minutes = 0
        if not matchmaking_data.is_first_refresh():
            tuned_cooldown_in_minutes = self.REFRESH_BUTTON_COOLDOWN().in_minutes()
            elapsed_time_delta_in_minutes = (current_time - last_refresh).in_minutes()
            if elapsed_time_delta_in_minutes > 0:
                if elapsed_time_delta_in_minutes < tuned_cooldown_in_minutes:
                    cooldown_time_left_in_minutes = tuned_cooldown_in_minutes - elapsed_time_delta_in_minutes
            else:
                cooldown_time_left_in_minutes = tuned_cooldown_in_minutes
        attracted_options = actor_info.get_attracted_genders(GenderPreferenceType.ROMANTIC)
        woohoo_options = actor_info.get_attracted_genders(GenderPreferenceType.WOOHOO)
        self.check_relationship(actor_info, list_matchmaking_profiles)
        self.check_hidden_relationship(actor_info, saved_profiles)
        remote_ids_on_cooldown = set(matchmaking_data.gallery_sims_on_cooldown.keys())
        for sim_id in valid_saved_ids:
            profile = self.candidate_id_to_matchmaking_profile[sim_id]
            if profile.profile_type == ProfileType.GALLERY_NPC:
                remote_ids_on_cooldown.add(profile.exchange_data_remote_id)
        remote_ids_on_cooldown.union(set(self.remote_id_to_sim_id.keys()))
        op = ShowMatchmakingDialog(actor_id, player_sim_profile_trait_ids, matchmaking_data.selected_ages, traits_selected, int(cooldown_time_left_in_minutes), matchmaking_data.num_contact_actions, list_matchmaking_profiles, saved_profiles, self.MAXIMUM_SAVE_LIMIT, self.DAILY_CONTACT_ACTIONS_LIMIT, attracted_options, woohoo_options, matchmaking_data.selfie_res_key, self.GALLERY_MINIMUM_DOWNLOAD_COUNT, self.GALLERY_UPLOAD_TIME_RANGE_START, self.GALLERY_UPLOAD_TIME_RANGE_END, matchmaking_data.bg_res_key, self.gallery_sims_enabled, self.gallery_sims_favorites_only_enabled, remote_ids_on_cooldown, is_update, is_traits_display_update)
        Distributor.instance().add_op(actor_info, op)

    def set_profile_thumbnail(self, candidate_id:'int', thumbnail_url:'str') -> 'Optional[int]':
        matchmaking_profile = self.candidate_id_to_matchmaking_profile[candidate_id]
        matchmaking_profile.thumbnail_url = thumbnail_url

    def contact_action_used(self, actor_info:'SimInfo', candidate_id:'int') -> 'Optional[int]':
        actor_id = actor_info.sim_id
        if actor_id not in self.actor_id_to_matchmaking_data:
            logger.error('Sim is not found in matchmaking service.')
            return
        matchmaking_data = self.actor_id_to_matchmaking_data[actor_id]
        matchmaking_profile = self.candidate_id_to_matchmaking_profile[candidate_id]
        if matchmaking_profile.rel_is_hidden:
            self.unhide_hidden_relationship(actor_info, matchmaking_profile)
        if matchmaking_profile.contacted:
            return matchmaking_profile.real_sim_id
        npc_info = matchmaking_profile.sim_info if matchmaking_profile.profile_type == ProfileType.WORLD_NPC else self.convert_base_sim_info_to_full(candidate_id)
        actor_info = services.sim_info_manager().get(actor_id)
        if npc_info is not None and actor_info is not None:
            npc_id = npc_info.sim_id
            rel_tracker = actor_info.relationship_tracker
            if not rel_tracker.has_relationship(npc_id):
                rel_tracker.create_relationship(npc_id)
                rel_tracker.add_relationship_score(npc_id, ON_CONTACT_NPC_REL_GAIN, RelationshipTrack.FRIENDSHIP_TRACK)
                rel_tracker.add_relationship_bit(npc_id, RelationshipGlobalTuning.HAS_MET_RELATIONSHIP_BIT)
                rel_tracker.add_relationship_bit(npc_id, RelationshipGlobalTuning.MATCHMAKING_RELATIONSHIP_BIT)
                knowledge = rel_tracker.get_knowledge(npc_id, initialize=True)
                if knowledge is not None:
                    trait_manager = services.get_instance_manager(sims4.resources.Types.TRAIT)
                    for trait_id in matchmaking_profile.displayed_traits_map.keys():
                        trait = trait_manager.get(trait_id)
                        if trait is not None:
                            knowledge.add_known_trait(trait)
                matchmaking_data.contact_action_used()
                matchmaking_profile.contacted = True
                matchmaking_profile.real_sim_id = npc_id
            return npc_id
        else:
            logger.error('Invalid NPC info for {}', npc_info)
            return

    def on_save_profile(self, actor_id:'int', candidate_id:'int') -> 'None':
        if actor_id not in self.actor_id_to_matchmaking_data:
            logger.error('Sim is not found in matchmaking service.')
            return
        sim_mm_data = self.actor_id_to_matchmaking_data[actor_id]
        saved_ids = sim_mm_data.saved_candidate_ids
        if candidate_id not in saved_ids and len(saved_ids) < self.MAXIMUM_SAVE_LIMIT:
            sim_mm_data.save_candidate(candidate_id)
        self.show_matchmaking_dialog(actor_id, True)

    def on_delete_profile(self, actor_id:'int', candidate_id:'int') -> 'None':
        if actor_id not in self.actor_id_to_matchmaking_data:
            logger.error('Sim is not found in matchmaking service.')
            return
        sim_mm_data = self.actor_id_to_matchmaking_data[actor_id]
        current_time = services.time_service().sim_now
        if candidate_id in self.candidate_id_to_matchmaking_profile:
            profile = self.candidate_id_to_matchmaking_profile[candidate_id]
            if profile.profile_type == ProfileType.WORLD_NPC:
                sim_mm_data.npcs_on_cooldown[candidate_id] = current_time
            elif profile.profile_type == ProfileType.GALLERY_NPC:
                sim_mm_data.gallery_sims_on_cooldown[profile.exchange_data_remote_id] = current_time
        sim_mm_data.remove_saved_candidate(candidate_id)
        self.show_matchmaking_dialog(actor_id, True)

    def on_report_gallery_profile(self, actor_id:'int', candidate_id:'int') -> 'None':
        if actor_id not in self.actor_id_to_matchmaking_data:
            logger.error('Sim is not found in matchmaking service.')
            return
        matchmaking_profile = self.candidate_id_to_matchmaking_profile[candidate_id]
        if matchmaking_profile is None:
            logger.error('Candidate Sim is not found in matchmaking service.')
            return
        matchmaking_profile.report_gallery_profile()
        self.show_matchmaking_dialog(actor_id, True)

    def set_selected_traits_for_sim_profile(self, sim_info:'SimInfo', traits:'Set[int]') -> 'None':
        matchmaking_data = self.actor_id_to_matchmaking_data[sim_info.sim_id]
        matchmaking_data.select_traits(traits)
        self.show_matchmaking_dialog(sim_info.sim_id, True, True)

    def set_traits_from_base_sim_info(self, sim_info:'SimInfo') -> 'None':
        trait_manager = services.get_instance_manager(sims4.resources.Types.TRAIT)
        base_traits = [trait_manager.get(trait_id) for trait_id in sim_info.base_trait_ids if trait_manager.get(trait_id) is not None]
        base_trait_types = [t.trait_type for t in base_traits]
        for trait in tuple(sim_info.trait_tracker):
            t_type = trait.trait_type
            if not t_type not in self.GENERATED_NPC_TRAIT_TYPE_ALLOWED:
                if t_type == TraitType.PERSONALITY:
                    sim_info.remove_trait(trait)
            sim_info.remove_trait(trait)
        for trait in base_traits:
            sim_info.add_trait(trait)

    def create_candidate_full_sim_info(self, candidate_id:'int') -> 'Tuple(Optional[SimInfo], Optional[int])':
        if candidate_id not in self.candidate_id_to_matchmaking_profile:
            logger.error('Candidate is not found in matchmaking service.')
            return (None, None)
        matchmaking_profile = self.candidate_id_to_matchmaking_profile[candidate_id]
        new_sim_info = None
        household = None
        if matchmaking_profile.profile_type != ProfileType.GALLERY_NPC:
            if matchmaking_profile.is_from_template:
                template = self.candidate_id_to_household_templates[matchmaking_profile.sim_id]
                household = template.create_household(None, creation_source='matchmaking', household_change_origin=HouseholdChangeOrigin.MATCHMAKING)
                new_sim_info = next(household.sim_info_gen())
                new_sim_info.first_name = matchmaking_profile.first_name
                self.remote_id_to_sim_id[matchmaking_profile.exchange_data_remote_id] = new_sim_info.sim_id
            else:
                sim_creator = SimCreator(age=matchmaking_profile.age, gender=matchmaking_profile.gender, species=Species.HUMAN, first_name=matchmaking_profile.first_name)
                (sim_info_list, household) = SimSpawner.create_sim_infos((sim_creator,), creation_source='matchmaking', household_change_origin=HouseholdChangeOrigin.MATCHMAKING)
                new_sim_info = sim_info_list[0]
            candidate_sim_info = matchmaking_profile.sim_info
            if candidate_sim_info is not None:
                SimInfoBaseWrapper.copy_physical_attributes(new_sim_info, candidate_sim_info)
                new_sim_info.pelt_layers = candidate_sim_info.pelt_layers
                new_sim_info.breed_name_key = candidate_sim_info.breed_name_key
                new_sim_info.load_outfits(candidate_sim_info.save_outfits())
                self.set_traits_from_base_sim_info(new_sim_info)
                new_sim_info.resend_physical_attributes()
            if matchmaking_profile.profile_type == ProfileType.GENERATED_NPC:
                self.real_id_to_generated_id[new_sim_info.sim_id] = candidate_id
        else:
            remote_id = matchmaking_profile.exchange_data_remote_id
            if remote_id in self.remote_id_to_sim_id:
                sim_id = self.remote_id_to_sim_id[remote_id]
                new_sim_info = services.sim_info_manager().get(sim_id)
                household = services.household_manager().get(new_sim_info.household_id)
            else:
                family_info_pb = matchmaking_profile.family_data
                for sim_proto in family_info_pb.sim:
                    sim_msg = services.get_persistence_service().add_sim_proto_buff(sim_proto.sim_id)
                    sim_msg.MergeFrom(sim_proto)
                household_manager = services.household_manager()
                household_msg = household_manager.family_info_proto_to_household_proto(matchmaking_profile.family_data)
                fixup_helper = HouseholdFixupHelper()
                household = household_manager.load_household_from_household_proto(household_msg, fixup_helper=fixup_helper)
                fixup_helper.fix_shared_sim_households()
                for sim_info in household.sim_info_gen():
                    if sim_info.sim_id == candidate_id:
                        new_sim_info = sim_info
                        break
                self.remote_id_to_sim_id[remote_id] = new_sim_info.sim_id
        new_sim_info.save_sim()
        household.save_data()
        return (new_sim_info, household)

    def convert_base_sim_info_to_full(self, candidate_id:'int') -> 'Optional[SimInfo]':
        (new_sim_info, new_household) = self.create_candidate_full_sim_info(candidate_id)
        return new_sim_info

    def save(self, save_slot_data:'serialization.SaveSlotData'=None, **kwargs):
        matchmaking_service_proto = save_slot_data.gameplay_data.matchmaking_service
        matchmaking_service_proto.gallery_kill_switch_enabled = self.gallery_kill_switch_enabled
        matchmaking_service_proto.ClearField('actor_sim_data')
        matchmaking_service_proto.ClearField('existing_npc_data')
        matchmaking_service_proto.ClearField('created_gallery_sims')
        for (sim_id, matchmaking_data) in self.actor_id_to_matchmaking_data.items():
            with ProtocolBufferRollback(matchmaking_service_proto.actor_sim_data) as actor_sim_data:
                matchmaking_data.save_actor_data(actor_sim_data)
                valid_candidate_ids = self.get_valid_npc_ids_from_list(matchmaking_data.candidate_ids)
                valid_saved_ids = self.get_valid_npc_ids_from_list(matchmaking_data.saved_candidate_ids)
                for npc_id in valid_candidate_ids.union(valid_saved_ids):
                    with ProtocolBufferRollback(matchmaking_service_proto.existing_npc_data) as existing_npc_data:
                        matchmaking_profile = self.candidate_id_to_matchmaking_profile[npc_id]
                        matchmaking_profile.save_profile(existing_npc_data)
                        if matchmaking_profile.is_from_template:
                            template = self.candidate_id_to_household_templates[matchmaking_profile.sim_id]
                            existing_npc_data.household_template_id = template.guid64
                        if matchmaking_profile.family_data is not None:
                            existing_npc_data.family_info_msg = matchmaking_profile.family_data.SerializeToString()
        for (remote_id, sim_id) in self.remote_id_to_sim_id.items():
            with ProtocolBufferRollback(matchmaking_service_proto.created_gallery_sims) as created_gallery_sim:
                created_gallery_sim.exchange_data_remote_id = remote_id
                created_gallery_sim.sim_id = sim_id

    def load(self, zone_data:'serialization.GameplayZoneData'=None):
        save_slot_data_msg = services.get_persistence_service().get_save_slot_proto_buff()
        matchmaking_service_data = save_slot_data_msg.gameplay_data.matchmaking_service
        self.gallery_kill_switch_enabled = matchmaking_service_data.gallery_kill_switch_enabled
        if hasattr(matchmaking_service_data, 'created_gallery_sims'):
            for created_gallery_sim in matchmaking_service_data.created_gallery_sims:
                self.remote_id_to_sim_id[created_gallery_sim.exchange_data_remote_id] = created_gallery_sim.sim_id
        for actor_data in matchmaking_service_data.actor_sim_data:
            matchmaking_data = MatchmakingData(actor_data.sim_id, actor_data.num_contact_actions)
            matchmaking_data.load_actor_data(actor_data)
            self.actor_id_to_matchmaking_data[actor_data.sim_id] = matchmaking_data
        for npc_data in matchmaking_service_data.existing_npc_data:
            profile = MatchmakingProfile(npc_data.sim_id, npc_data.profile_type, npc_data.first_name, npc_data.age, npc_data.gender, npc_data.displayed_trait_ids)
            profile_type = profile.profile_type
            profile.region_name = npc_data.region_name
            profile.contacted = npc_data.contacted
            profile.real_sim_id = npc_data.real_sim_id
            profile.reported = npc_data.reported
            profile.is_from_template = npc_data.is_from_template
            profile.pose_index = npc_data.pose_index
            if profile.is_from_template:
                for weighted_template in self.RANDOM_HOUSEHOLD_TEMPLATES:
                    if npc_data.household_template_id == weighted_template.household_template.guid64:
                        self.candidate_id_to_household_templates[profile.sim_id] = weighted_template.household_template
            if profile_type == ProfileType.GENERATED_NPC or profile_type == ProfileType.GALLERY_NPC:
                sim_info = SimInfoBaseWrapper(sim_id=npc_data.sim_id)
                sim_info.load_sim_info(npc_data)
                profile.sim_info = sim_info
                sim_info.set_trait_ids_on_base(trait_ids_override=list(npc_data.trait_ids))
            if profile_type == ProfileType.GENERATED_NPC:
                real_sim_id = profile.real_sim_id
                if real_sim_id != 0:
                    self.real_id_to_generated_id[real_sim_id] = profile.sim_id
            if profile_type == ProfileType.GALLERY_NPC:
                profile.trait_ids = list(npc_data.trait_ids)
                profile.exchange_data_household_id = npc_data.exchange_data_household_id
                profile.exchange_data_creator_name = npc_data.exchange_data_creator_name
                profile.exchange_data_remote_id = npc_data.exchange_data_remote_id
                profile.exchange_data_type = npc_data.exchange_data_type
            if has_field(npc_data, 'profile_bg_res_key'):
                profile.profile_bg_res_key = sims4.resources.Key()
                profile.profile_bg_res_key.type = npc_data.profile_bg_res_key.type
                profile.profile_bg_res_key.group = npc_data.profile_bg_res_key.group
                profile.profile_bg_res_key.instance = npc_data.profile_bg_res_key.instance
            if has_field(npc_data, 'family_info_msg'):
                profile.family_data = Sims_pb2.AccountFamilyData()
                profile.family_data.ParseFromString(npc_data.family_info_msg)
            self.candidate_id_to_matchmaking_profile[npc_data.sim_id] = profile

    def on_all_households_and_sim_infos_loaded(self, _):
        save_slot_data = services.get_persistence_service().get_save_slot_proto_buff()
        sim_info_manager = services.sim_info_manager()
        for npc_data in save_slot_data.gameplay_data.matchmaking_service.existing_npc_data:
            profile = self.candidate_id_to_matchmaking_profile[npc_data.sim_id]
            if npc_data.profile_type == ProfileType.GENERATED_NPC or npc_data.profile_type == ProfileType.GALLERY_NPC:
                if profile is not None:
                    profile.sim_info.manager = services.sim_info_manager()
                    Distributor.instance().add_object(profile.sim_info)
                    if npc_data.profile_type == ProfileType.WORLD_NPC:
                        sim_info = sim_info_manager.get(npc_data.sim_id)
                        if profile is not None and sim_info is not None:
                            profile.real_sim_id = sim_info.sim_id
                            profile.sim_info = sim_info
            elif npc_data.profile_type == ProfileType.WORLD_NPC:
                sim_info = sim_info_manager.get(npc_data.sim_id)
                if profile is not None and sim_info is not None:
                    profile.real_sim_id = sim_info.sim_id
                    profile.sim_info = sim_info
        for actor_data in save_slot_data.gameplay_data.matchmaking_service.actor_sim_data:
            actor_info = sim_info_manager.get(actor_data.sim_id)
            if actor_info is not None:
                attraction_preferences = set(filter(lambda trait: trait.is_attraction_trait, actor_info.trait_tracker))
                for preference in attraction_preferences:
                    for npc_id in actor_data.candidate_ids:
                        if npc_id in self.candidate_id_to_matchmaking_profile:
                            npc_profile = self.candidate_id_to_matchmaking_profile[npc_id]
                            if npc_profile is not None:
                                trait_manager = services.get_instance_manager(sims4.resources.Types.TRAIT)
                                for trait_id in npc_profile.displayed_traits_map:
                                    npc_profile.displayed_traits_map[trait_id] += int(self.calculate_preference_score_for_trait(preference, trait_manager.get(trait_id)))

    def on_zone_load(self):
        for (candidate_id, profile) in self.candidate_id_to_matchmaking_profile.items():
            if profile.profile_type == ProfileType.WORLD_NPC:
                pass
            else:
                Distributor.instance().add_object(profile.sim_info)
