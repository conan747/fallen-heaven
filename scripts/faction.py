__author__ = 'cos'





class Faction(object):
    '''
    Holds the information about a faction i.e. a player and all its units and resources.
    '''


    # _RES_ENERGY, _RES_CREDITS, _RES_RESEARCH = xrange(3)

    def __init__(self, name= "Human", factionInfo=None):

        if factionInfo:
            self.__setInfo__(factionInfo)
            return

        self.resources = {"Energy": 0,
                     "Credits" : 0,
                     "Research" : 0}

        self.technology = {"Energy" : 1,
                      "Armor" : 1,
                      "Movement" : 1,
                      "Damage" : 1,
                      "RateOfFire" : 1,
                      "Rocketry" : 1}

        self.name = name

        if self.name == "Human":
            self.pwnedPlanets = ["firstCapital"]
        else:
            self.pwnedPlanets = ["enemyPlanet"]



    def __setInfo__(self, factionInfo):
        [setattr(self, info, factionInfo[info]) for info in factionInfo.keys()]

    def __getInfo__(self):

        factionDict = {}
        for member in dir(self):
            if not member.startswith("__"):
                factionDict[member] = getattr(self, member)

        return factionDict
