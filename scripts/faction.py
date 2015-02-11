__author__ = 'cos'





class Faction(object):
    '''
    Holds the information about a faction i.e. a player and all its units and resources.
    '''
    name = None
    pwnedPlanets = []
    resources = None
    technology = None

    # _RES_ENERGY, _RES_CREDITS, _RES_RESEARCH = xrange(3)

    def __init__(self, name= ""):
        resources = {"Energy": 0,
                     "Credits" : 0,
                     "Research" : 0}

        technology = {"Energy" : 1,
                      "Armor" : 1,
                      "Movement" : 1,
                      "Damage" : 1,
                      "RateOfFire" : 1,
                      "Rocketry" : 1}

        self.name = name

        self.pwnedPlanets.append("firstCapital")

    def __setInfo__(self, factionInfo):
        [setattr(self, info, factionInfo[info]) for info in factionInfo.keys()]

