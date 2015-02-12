__author__ = 'cos'


import cPickle as pickle
import os

class Progress(object):
    '''
    Tracks the current progress to save/restore games.
    '''



    def __init__(self, universe):
        '''

        :return:
        '''
        self.universe = universe # Points at the universe

        self.playerFactionName = "Human"
        self.saveDir = "saves/test/"    # Directory where the file should be saved/loaded
        self.allPlanets = {} # Dictionary containing planet name:planetInfo
        self.factions = {} # Dictionary containing faction name:factionInfo.

        # Dictionary containing all the information. Will be saved/loaded.
        self.progressDict = {"playerFactionName" : self.playerFactionName,
                             "saveDir" : self.saveDir}

        self.playerName = ""
        self.waitingForResponse = False


    def update(self):

        # Update Faction
        faction = self.universe.faction
        print dir(faction)
        factionDict = {}
        for member in dir(faction):
            if not member.startswith("__"):
                factionDict[member] = getattr(faction, member)

        self.factions[factionDict["name"]] = factionDict
        self.progressDict["factions"] = self.factions



        # Update open planet:
        if self.universe.world.planet:
            self.universe.world.scene.updatePlanetAgents()
            storages = self.universe.world.scene.getStorageDicts()
            planetDict = self.universe.world.planet.getPlanetDict()
            planetDict["storages"] = storages
            self.allPlanets[planetDict["name"]] = planetDict

        self.progressDict["allPlanets"] = self.allPlanets

        self.progressDict["waitingForResponse"] = self.waitingForResponse


    def save(self):

        self.update()

        saveFile = self.saveDir + self.playerName + ".prg"
        pickle.dump(self.progressDict, open(saveFile, 'wb'))


    def load(self, fileName):

        assert os.path.isfile(fileName) , "File %r could not be loaded!" % fileName
        self.progressDict = pickle.load(open(fileName, 'rb'))

        assert self.progressDict, "Empty file loaded!"

        [setattr(self, attr, self.progressDict[attr]) for attr in self.progressDict.keys()]










