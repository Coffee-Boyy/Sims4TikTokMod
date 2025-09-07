from __future__ import annotationsfrom gsi_handlers.gameplay_archiver import GameplayArchiverfrom sims4.gsi.schema import GsiGridSchemafrom typing import TYPE_CHECKINGif TYPE_CHECKING:
    from typing import *
class LuckArchiveEntry:
    __slots__ = ('source', 'choice_data', 'returned_luck_selection', 'returned_luck_level')

    def __init__(self, source:'str') -> 'None':
        self.source = source
        self.choice_data = None
        self.returned_luck_selection = False
        self.returned_luck_level = False
luck_archive = GsiGridSchema(label='Luck Archive')luck_archive.add_field('source', label='Source')luck_archive.add_field('target', label='Target Sim')luck_archive.add_field('returned_luck_selection', label='Did Luck Influence Choice?')luck_archive.add_field('returned_luck_level', label='Did Luck Advertise Influence?')luck_archive.add_field('luck_level', label='Luck Level')luck_archive.add_field('normal_selection_index', label='Selection Index Without Luck')luck_archive.add_field('luck_selection_index', label='Selection Index With Luck')luck_archive.add_field('normal_selection_perception', label='Perception of Normal Selection')luck_archive.add_field('luck_selection_perception', label='Perception of Luck Selection')with luck_archive.add_has_many('input_options', GsiGridSchema, label='Input Options') as sub_schema:
    sub_schema.add_field('weight', label='Weight')
    sub_schema.add_field('perceived_value', label='Perceived Value')
    sub_schema.add_field('luck_weight', label='Luck Weight')
    sub_schema.add_field('option', label='Option')archiver = GameplayArchiver('luck_archive', luck_archive)
def add_luck_archive_entry(archive_entry:'LuckArchiveEntry') -> 'None':
    if True or not archiver.enabled:
        return
    entry = {'source': archive_entry.source, 'target': 'N/A', 'returned_luck_selection': archive_entry.returned_luck_selection, 'returned_luck_level': archive_entry.returned_luck_level, 'luck_level': 'N/A', 'input_options': [], 'normal_selection_index': 'N/A', 'luck_selection_index': 'N/A', 'normal_selection_perception': archive_entry.choice_data.normal_selection_perception, 'luck_selection_perception': archive_entry.choice_data.luck_selection_perception}
    if archive_entry.choice_data.target is not None:
        entry['target'] = archive_entry.choice_data.target.full_name
    if archive_entry.choice_data.luck_level is not None:
        entry['luck_level'] = repr(archive_entry.choice_data.luck_level())
    if archive_entry.choice_data.normal_selection is not None:
        entry['normal_selection_index'] = archive_entry.choice_data.normal_selection.selection_index
    if archive_entry.choice_data.luck_selection is not None:
        entry['luck_selection_index'] = archive_entry.choice_data.luck_selection.selection_index
    luck_weights = archive_entry.choice_data.luck_weights
    has_luck_weights = len(luck_weights) > 0
    for (index, option) in enumerate(archive_entry.choice_data.input_options):
        entry['input_options'].append({'weight': option.weight, 'perceived_value': option.perceived_value, 'luck_weight': luck_weights[index] if has_luck_weights else None, 'option': repr(option.user_data)})
    archiver.archive(data=entry)
