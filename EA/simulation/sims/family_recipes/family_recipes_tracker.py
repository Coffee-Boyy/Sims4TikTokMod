from __future__ import annotationsfrom typing import TYPE_CHECKINGif TYPE_CHECKING:
    from typing import *
    from sims.sim_info import SimInfo
    from crafting.recipe import Recipeimport sims4.logimport servicesfrom sims.sim_info_tracker import SimInfoTrackerfrom distributor.rollback import ProtocolBufferRollbackfrom sims.family_recipes.family_recipes_tuning import FamilyRecipesTuningfrom notebook.notebook_entry import SubEntryDatafrom sims4.utils import classpropertyfrom sims4.common import Packfrom event_testing.resolver import SingleSimResolverfrom element_utils import build_elementfrom objects import ALL_HIDDEN_REASONS_EXCEPT_UNINITIALIZEDlogger = sims4.log.Logger('FamilyRecipeTracker', default_owner='rahissamiyordi')
class FamilyRecipe:
    __annotations__['recipe_id'] = 'int'
    __annotations__['recipe_name'] = 'str'
    __annotations__['ingredient_id'] = 'int'
    __annotations__['buff_id'] = 'int'
    __annotations__['recipe_owner'] = 'str'

    def __init__(self, recipe_id:'int', recipe_name:'str', ingredient_id:'int', buff_id:'int', recipe_owner:'str'):
        self.recipe_id = recipe_id
        self.recipe_name = recipe_name
        self.ingredient_id = ingredient_id
        self.buff_id = buff_id
        self.recipe_owner = recipe_owner

    def __eq__(self, other):
        return isinstance(other, FamilyRecipe) and (self.buff_id == other.buff_id and (self.recipe_id == other.recipe_id and (self.recipe_name == other.recipe_name and (self.ingredient_id == other.ingredient_id and self.recipe_owner == other.recipe_owner))))

    def __hash__(self):
        return hash((self.recipe_id, self.recipe_name, self.ingredient_id, self.buff_id, self.recipe_owner))

class FamilyRecipesTracker(SimInfoTracker):

    def __init__(self, sim_info:'SimInfo'):
        self._owner = sim_info
        self._family_recipes = []
        self._initial_loot_applied = False

    def on_lod_update(self, old_lod, new_lod):
        if not self.is_valid_for_lod(new_lod):
            self._clean_up()

    def _clean_up(self):
        self._owner = None
        self._family_recipes = []

    @classproperty
    def required_packs(cls):
        return (Pack.EP18,)

    @property
    def sim_info(self):
        return self._sim_info

    def save_family_recipes(self, family_recipes_data):
        family_recipes_data.initial_loot_applied = self._initial_loot_applied
        for family_recipe_item in self._family_recipes:
            with ProtocolBufferRollback(family_recipes_data.family_recipes) as family_recipe:
                family_recipe.recipe_id = family_recipe_item.recipe_id
                family_recipe.recipe_name = family_recipe_item.recipe_name
                family_recipe.ingredient_id = family_recipe_item.ingredient_id
                family_recipe.buff_id = family_recipe_item.buff_id
                family_recipe.recipe_owner = family_recipe_item.recipe_owner

    def load_family_recipes(self, family_recipes_data):
        self._initial_loot_applied = family_recipes_data.initial_loot_applied
        for family_recipe in family_recipes_data.family_recipes:
            self._family_recipes.append(family_recipe)

    def add_family_recipe(self, family_recipe:'FamilyRecipe') -> 'None':
        self._family_recipes.append(family_recipe)
        self.add_family_recipe_notebook_entry(family_recipe, self._owner)

    def get_family_recipes(self):
        return self._family_recipes

    def get_family_recipe_by_buff(self, buff_id:'int') -> 'Optional[FamilyRecipe]':
        for family_recipe in self._family_recipes:
            if family_recipe.buff_id == buff_id:
                return family_recipe

    def replace_family_recipe(self, old_family_recipe:'FamilyRecipe', new_family_recipe:'FamilyRecipe') -> 'None':
        index = self._family_recipes.index(old_family_recipe)
        self._family_recipes[index] = new_family_recipe
        notebook_tracker = self._owner.notebook_tracker
        if notebook_tracker is None:
            return
        notebook_tracker.remove_entry_by_object_definition_id(old_family_recipe.buff_id, FamilyRecipesTuning.FAMILY_RECIPE_NOTEBOOK_DATA.reference_notebook_entry.subcategory_id)
        self.add_family_recipe_notebook_entry(new_family_recipe, self._owner)

    @staticmethod
    def add_family_recipe_notebook_entry(family_recipe:'FamilyRecipe', sim_info:'SimInfo') -> 'None':
        if sim_info.notebook_tracker is None:
            return
        sub_entries = (SubEntryData(family_recipe.recipe_id, True),)
        sim_info.notebook_tracker.unlock_entry(FamilyRecipesTuning.FAMILY_RECIPE_NOTEBOOK_DATA.reference_notebook_entry(family_recipe.buff_id, sub_entries=sub_entries))

    def get_family_recipe_cost_modifier(self, recipe:'Recipe') -> 'float':
        cost_modifier_size = 1
        for state in recipe.final_product.apply_states:
            if state in FamilyRecipesTuning.FAMILY_RECIPE_DATA.cost_modifier_based_on_size:
                cost_modifier_size = FamilyRecipesTuning.FAMILY_RECIPE_DATA.cost_modifier_based_on_size[state]
                break
        return cost_modifier_size

    def apply_retroactive_buff_unlocks(self):
        if self._initial_loot_applied:
            return
        is_instanced = self._owner.is_instanced(allow_hidden_flags=ALL_HIDDEN_REASONS_EXCEPT_UNINITIALIZED)
        zone_is_running = services.current_zone().is_zone_running
        if is_instanced:
            if zone_is_running:
                self._apply_retroactive_buff_unlocks_from_gameplay()
            else:
                self._apply_initial_loot()

    def _apply_retroactive_buff_unlocks_from_gameplay(self):
        self._apply_initial_loot(from_gameplay=True)

        def _post_retroactive_actions(*_):
            self._initial_loot_applied = True

        element = build_element([_post_retroactive_actions])
        services.time_service().sim_timeline.schedule(element)

    def _apply_initial_loot(self, from_gameplay:'bool'=False):
        resolver = SingleSimResolver(self._owner)
        for loot_entry in FamilyRecipesTuning.FAMILY_RECIPE_DATA.retroactive_buff_unlocks:
            loot_entry.apply_to_resolver(resolver)
        if not from_gameplay:
            self._initial_loot_applied = True
