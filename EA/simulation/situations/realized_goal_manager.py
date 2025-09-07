from __future__ import annotationsfrom typing import TYPE_CHECKINGif TYPE_CHECKING:
    from typing import Tuple, Optional, List
    from situations.situation_goal import SituationGoalimport sims4.loglogger = sims4.log.Logger('RealizedGoalManager', default_owner='hbarcelos')
class RealizedGoalManager:
    MAX_GOALS = 3
    __annotations__['MAX_GOALS'] = 'int'

    def __init__(self) -> 'None':
        self.goals = [None]*self.MAX_GOALS

    def __len__(self):
        return sum(1 for goal in self.goals if goal is not None)

    def destroy(self) -> 'None':
        self.goals = None

    def add_goal(self, new_goal:'SituationGoal') -> 'bool':
        for (i, goal) in enumerate(self.goals):
            if goal is None:
                self.goals[i] = new_goal
                return True
        return False

    def can_add_new_goal(self) -> 'bool':
        return any(goal is None for goal in self.goals)

    def is_goal_realized(self, looking_for_goal:'SituationGoal') -> 'bool':
        for goal in self.goals:
            if goal is not None and goal.guid64 == looking_for_goal.guid64:
                return True
        return False

    def remove_goal_completed(self, completed_goal:'SituationGoal') -> 'None':
        for (i, goal) in enumerate(self.goals):
            if goal and goal.guid64 == completed_goal.guid64:
                self.goals[i] = None
                return

    def get_goals(self) -> 'Tuple[SituationGoal, ...]':
        return tuple(self.goals)
