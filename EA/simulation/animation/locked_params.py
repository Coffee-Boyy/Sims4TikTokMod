from __future__ import annotationsfrom typing import TYPE_CHECKINGif TYPE_CHECKING:
    from typing import *from sims4.collections import frozendictfrom sims4.log import Loggerimport enumlogger = Logger('Locked Params', default_owner='myakubek')
class LockedParamCategory(enum.Int, export=False):
    INTERACTION = 1
    SIM_TRAIT = 2
    SIM_ANIM = 3
    TARGET_ANIM = 4
    TARGET_PART = 5
    JIG = 6
    POSTURE = 7
    POSTURE_DEST = 8
    OUTFIT = 9

class LockedParamsContext:
    __slots__ = ('_category', '_source', '_notes', '_current_value')

    def __init__(self, category:'LockedParamCategory', source:'Optional[str]'=None, notes:'Optional[str]'=None, param_val:'Optional[Any]'=None) -> 'None':
        self._category = category
        self._source = source
        self._notes = notes
        self._current_value = param_val

    def __str__(self) -> 'str':
        return 'Value: {}. ({} change from {}.) Notes: {}'.format(self._current_value, self._category.name, self._source, self._notes)

    def get_with_value(self, new_value:'Any') -> 'LockedParamsContext':
        return LockedParamsContext(self._category, self._source, self._notes, new_value)

    @property
    def category(self) -> 'LockedParamCategory':
        return self._category

    @property
    def source(self) -> 'Optional[str]':
        return self._source

    @property
    def notes(self) -> 'Optional[str]':
        return self._notes

    @property
    def current_value(self) -> 'Any':
        return self._current_value

def create_locked_params_log(locked_params:'frozendict', creation_context:'LockedParamsContext') -> 'frozendict':
    locked_params_log = frozendict()
    for param_name in locked_params.keys():
        context = creation_context.get_with_value(locked_params[param_name])
        locked_params_log += {param_name: (context,)}
    return locked_params_log

def add_context_to_locked_params_log(locked_params_log:'Optional[frozendict]', param_name:'Any', context:'LockedParamsContext') -> 'frozendict':
    return add_context_tuple_to_locked_params_log(locked_params_log, param_name, (context,))

def add_context_tuple_to_locked_params_log(locked_params_log:'Optional[frozendict]', param_name:'Any', context_tuple:'Tuple[LockedParamsContext]') -> 'frozendict':
    if locked_params_log is None:
        return frozendict({param_name: context_tuple})
    if param_name not in locked_params_log:
        return locked_params_log + {param_name: context_tuple}
    combined_context = locked_params_log[param_name] + context_tuple
    return locked_params_log + {param_name: combined_context}

def add_multiple_contexts_to_locked_params_log(locked_params_log:'frozendict', param_dict:'frozendict', update_context:'LockedParamsContext') -> 'frozendict':
    for (param_name, param_value) in param_dict.items():
        context = update_context.get_with_value(param_value)
        locked_params_log = add_context_to_locked_params_log(locked_params_log, param_name, context)
    return locked_params_log
