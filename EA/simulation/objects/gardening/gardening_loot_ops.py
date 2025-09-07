from __future__ import annotationsimport placementimport servicesimport sims4.logfrom event_testing.resolver import SingleObjectResolver, Resolver, DoubleObjectResolverfrom event_testing.tests import TunableTestSetfrom interactions import ParticipantTypefrom interactions.utils.loot_basic_op import BaseLootOperationfrom objects import VisibilityStatefrom objects.system import create_objectfrom sims4.random import weighted_random_itemfrom sims4.resources import Typesfrom sims4.tuning.tunable import TunableList, TunableTuple, TunableReference, TunableEnumEntryfrom tunable_multiplier import TunableMultiplierfrom tunable_utils.tunable_object_generator import TunableObjectGeneratorVariantfrom typing import TYPE_CHECKINGif TYPE_CHECKING:
    from typing import *
    from objects.game_object import GameObject
    from interactions.utils.loot import LootActions
    from sims.sim_info import SimInfologger = sims4.log.Logger('GardeningLootOps', default_owner='jdimailig')
class CreatePlantAtLocationLootOperation(BaseLootOperation):
    FACTORY_TUNABLES = {'fruits_to_sprout_from': TunableList(description='\n            A list of weighted fruit definitions we want to create a plant from.\n            ', tunable=TunableTuple(description='\n                The fruit to spawn a plant.\n                ', fruit=TunableReference(manager=services.get_instance_manager(Types.OBJECT), pack_safe=True), weight=TunableMultiplier.TunableFactory()), minlength=1), 'states_to_set_on_plant': TunableList(description='\n            The states to set on the created plant.\n            ', tunable=TunableReference(manager=services.get_instance_manager(Types.OBJECT_STATE), class_restrictions=('ObjectStateValue',), pack_safe=True), unique_entries=True)}

    def __init__(self, *args, fruits_to_sprout_from, states_to_set_on_plant, **kwargs):
        super().__init__(*args, **kwargs)
        self._fruits_to_sprout_from = fruits_to_sprout_from
        self._states_to_set_on_plant = states_to_set_on_plant

    def _apply_to_subject_and_target(self, subject, target, resolver):
        if not self._fruits_to_sprout_from:
            return
        weighted_fruit_definitions = list((weighted_fruit.weight.get_multiplier(resolver), weighted_fruit.fruit) for weighted_fruit in self._fruits_to_sprout_from)
        fruit_to_germinate = sims4.random.pop_weighted(weighted_fruit_definitions)
        parent_slot = None
        if not subject.is_terrain:
            runtime_slots = tuple(subject.get_runtime_slots_gen())
            fruit_to_try = fruit_to_germinate
            fruit_to_germinate = None
            while fruit_to_germinate is None:
                for slot in runtime_slots:
                    if not slot.empty:
                        pass
                    elif slot.is_valid_for_placement(definition=fruit_to_try):
                        fruit_to_germinate = fruit_to_try
                        parent_slot = slot
                        break
                if fruit_to_germinate is not None:
                    break
                if not weighted_fruit_definitions:
                    break
                fruit_to_try = sims4.random.pop_weighted(weighted_fruit_definitions)

        def post_add(obj):
            obj.transient = True
            obj.visibility = VisibilityState(visibility=False, inherits=False, enable_drop_shadow=False)

        created_fruit = create_object(fruit_to_germinate, post_add=post_add)
        if created_fruit is None:
            logger.error(f'Error occurred creating {fruit_to_germinate} in {self}')
            return
        if created_fruit.gardening_component is None:
            logger.error(f'{created_fruit} is a fruit with no fruit gardening component tuned in {self}')
            return
        if parent_slot is None:
            starting_location = placement.create_starting_location(position=subject.position, routing_surface=subject.routing_surface)
            fgl_context = placement.create_fgl_context_for_object(starting_location, created_fruit, ignored_object_ids=(created_fruit.id,))
            (position, orientation, _) = fgl_context.find_good_location()
            if position is None or orientation is None:
                logger.warn(f'Could not find good location for {created_fruit} using starting location {starting_location}')
                return
            created_fruit.move_to(translation=position, orientation=orientation, routing_surface=subject.routing_surface)
        else:
            parent_slot.add_child(created_fruit)
        created_plant = created_fruit.gardening_component.germinate()
        if not created_plant:
            logger.error(f'Failed to germinate {created_fruit}')
            return
        for state_to_set in self._states_to_set_on_plant:
            created_plant.set_state(state_to_set.state, state_to_set)
        if created_plant.gardening_component is None:
            logger.error(f'{created_plant} was germinated but had no gardening component!')
            return
        if resolver.interaction:
            resolver.interaction.context.create_target_override = created_plant

class FertilizeAll(BaseLootOperation):
    FACTORY_TUNABLES = {'plants_to_fertilize': TunableTuple(description='\n            The plants to generate and the tests they must pass in \n            order to be fertilized \n            ', plants=TunableObjectGeneratorVariant(description='\n                The plants to retrieve.\n                ', participant_default=ParticipantType.Object), tests=TunableTestSet(description='\n                Tests that will run on each generated object. For each object, if the\n                tests pass, a tuned Loot List will be applied to the object.\n                ')), 'fertilizer_type_loots': TunableList(description='\n            Tests that will run on each each potential fertilizer in the picked stack. \n            For each potential fertilizer, if the fertilizer type tests pass, \n            the paired loot list will be applied to the plant.\n            ', tunable=TunableTuple(fertilizer_type_tests=TunableTestSet(), loot_list=TunableList(tunable=TunableReference(manager=services.get_instance_manager(sims4.resources.Types.ACTION), class_restrictions=('LootActions',), pack_safe=True)))), 'picked_fertilizer_object': TunableEnumEntry(description='\n            ParticipantType used to get the object stack id.\n            ', tunable_type=ParticipantType, default=ParticipantType.PickedObject)}

    def __init__(self, *args, plants_to_fertilize, fertilizer_type_loots, picked_fertilizer_object, **kwargs):
        super().__init__(*args, **kwargs)
        self.plants_to_fertilize = plants_to_fertilize
        self.fertilizer_type_loots = fertilizer_type_loots
        self.picked_fertilizer_object = picked_fertilizer_object

    def _apply_to_subject_and_target(self, subject:'SimInfo', target:'SimInfo', resolver:'Resolver') -> 'None':
        plants_to_fertilize = self._get_plants_to_fertilize(resolver)
        if not plants_to_fertilize:
            return
        picked_fertilizer = resolver.get_participant(self.picked_fertilizer_object)
        fertilizer_stack_objects = self._get_fertilizer_stack_objects(picked_fertilizer)
        if not fertilizer_stack_objects:
            return
        fertilizers_count = sum(obj.stack_count() for obj in fertilizer_stack_objects)
        num_to_fertilize = min(fertilizers_count, len(plants_to_fertilize))
        fertilizer_index = 0
        for i in range(num_to_fertilize):
            plant = plants_to_fertilize[i]
            fertilizer = None
            if fertilizer_stack_objects[fertilizer_index].stack_count() > 1:
                fertilizer = fertilizer_stack_objects[fertilizer_index].try_split_object_from_stack(count=fertilizer_stack_objects[fertilizer_index].stack_count() - 1)
            else:
                fertilizer = fertilizer_stack_objects[fertilizer_index]
                fertilizer_index += 1
            fertilizer_loots = self._get_valid_fertilizer_loots(fertilizer, plant)
            if not fertilizer_loots:
                pass
            else:
                fertilizer_loots_resolver = resolver.interaction.get_resolver(target=plant)
                fertilizer_loots_resolver.interaction_parameters['picked_item_ids'] = {fertilizer.id}
                for loot in fertilizer_loots:
                    loot.apply_to_resolver(fertilizer_loots_resolver)
                fertilizer.transient = True

    def _get_plants_to_fertilize(self, resolver:'Resolver') -> 'List[GameObject]':
        plants_to_fertilize = []
        for plant in self.plants_to_fertilize.plants.get_objects(resolver=resolver):
            plant_resolver = SingleObjectResolver(plant)
            if not self.plants_to_fertilize.tests.run_tests(plant_resolver):
                pass
            else:
                plants_to_fertilize.append(plant)
        return plants_to_fertilize

    @staticmethod
    def _get_fertilizer_stack_objects(picked_fertilizer:'GameObject') -> 'List[GameObject]':
        fertilizer_stack_objects = []
        if picked_fertilizer is None or picked_fertilizer.inventoryitem_component is None:
            return fertilizer_stack_objects
        fertilizer_stack_id = picked_fertilizer.inventoryitem_component.get_stack_id()
        inventory = picked_fertilizer.get_inventory()
        if not inventory:
            return fertilizer_stack_objects
        for obj in inventory.get_stack_items(fertilizer_stack_id):
            fertilizer_stack_objects.append(obj)
        return fertilizer_stack_objects

    def _get_valid_fertilizer_loots(self, fertilizer:'GameObject', plant:'GameObject') -> 'List[LootActions]':
        resolver = DoubleObjectResolver(fertilizer, plant)
        for fertilizer_loot in self.fertilizer_type_loots:
            if not fertilizer_loot.fertilizer_type_tests.run_tests(resolver):
                pass
            else:
                return fertilizer_loot.loot_list
        return []
