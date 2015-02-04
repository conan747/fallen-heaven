__author__ = 'cos'



class Progress(object):
    '''
    Tracks the current progress to save/restore games.
    '''

    progressDict = {}

    def __init__(self, universe):
        '''

        :return:
        '''
        self.universe = universe
        faction = self.universe.faction
        print dir(faction)
        factionDict = {}
        for member in dir(faction):
            if not member.startswith("__"):
                factionDict[member] = getattr(faction, member)

        self.progressDict["Faction"] = factionDict

        for planet in faction.pwnedPlanets:
            pass




