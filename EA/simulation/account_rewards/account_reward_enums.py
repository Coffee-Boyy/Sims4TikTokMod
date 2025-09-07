import enum
class AccountRewardType(enum.Int, export=False):
    UNKNOWN = 0
    CAS = 1
    BUILDBUY = 2
    TRAIT = 3
    LOTTRAIT = 4
    CONSUMABLE = 5
    RECIPE = 6
    ASPIRATIONTRACK = 7
    RADIOSONG = 8
    CATALOGPRODUCT_FLOORPATTERN = 9
    CATALOGPRODUCT_WALLPATTERN = 10
    RADIOSTATION = 11
