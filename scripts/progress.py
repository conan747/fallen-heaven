__author__ = 'cos'


import cPickle as pickle
import os

class Progress(object):
    '''
    Tracks the current progress to save/restore games.
    '''



    def __init__(self, universe, playerFactionName="Human"):
        '''

        :return:
        '''
        self.universe = universe # Points at the universe

        self.playerFactionName = playerFactionName
        self.saveDir = "saves/test/"    # Directory where the file should be saved/loaded
        self.allPlanets = {} # Dictionary containing planet name:planetInfo
        self.factionInfo = None # Dictionary containing faction factionInfo.

        # Dictionary containing all the information. Will be saved/loaded.
        self.progressDict = {"playerFactionName" : self.playerFactionName,
                             "saveDir" : self.saveDir}

        self.playerName = ""
        self.waitingForResponse = False
        self.attacking = [] # list containing the "Attacking info" of the dropships of this player.
        ## It will contain: {"origin": <name of the planet of origin>,
        ##                  "target": <name of the destination planet>
        ##                  "storage": <storage dictionary that this dropship has>


    def update(self):

        # Update Faction
        faction = self.universe.faction

        self.factionInfo = faction.__getInfo__()
        self.progressDict["factionInfo"] = self.factionInfo

        # Update open planet:
        if self.universe.world:
            if self.universe.world.planet:
                self.universe.world.scene.updatePlanetAgents()
                storages = self.universe.world.scene.getStorageDicts()
                planetDict = self.universe.world.planet.getPlanetDict()
                planetDict["storages"] = storages
                self.allPlanets[planetDict["name"]] = planetDict

        self.progressDict["allPlanets"] = self.allPlanets
        self.progressDict["playerName"] = self.playerName

        self.progressDict["waitingForResponse"] = self.waitingForResponse

        # Updating Attacking list
        self.progressDict["attacking"] = self.attacking
        ## TODO: Check if we updated the fact that a planet was conquered -> Check pwnedPlanets!


    def save(self):

        self.update()

        saveFile = self.saveDir + self.playerName + ".prg"
        pickle.dump(self.progressDict, open(saveFile, 'wb'))


    def load(self, fileName):

        assert os.path.isfile(fileName) , "File %r could not be loaded!" % fileName
        self.progressDict = pickle.load(open(fileName, 'rb'))

        assert self.progressDict, "Empty file loaded!"

        [setattr(self, attr, self.progressDict[attr]) for attr in self.progressDict.keys()]










