__author__ = 'cos'


from progress import Progress
import cPickle as pickle
import os
from faction import Faction


class Campaign(object):
    '''
    Campaign object deals with the information exchange between players.
    '''

    def __init__(self, universe):
        self.universe = universe
        self.planetList = self.getPlanetNames()
        self.year = 0 # Strategic turn
        self.turn = 0 # Tactic turn


    def newCampaign(self):
        self.players = {"Me" : "Human" ,
                        "You" : "Tauran"}
        factionNames = ["Human" , "Tauran"]

        for player in self.players.keys():
            progress = Progress(self.universe)
            progress.playerFactionName = self.players[player]
            self.players[player] = progress

        for progress in self.players.values():
            for factionName in factionNames:
                progress.factions[factionName] = Faction(factionName)

        print self.players


    def getPlanetNames(self):
        '''
        Gets a list of planet names from the map directory
        :return:
        '''
        fileNames = os.listdir("maps")
        planetNames = [fileName.split(".xml")[0] for fileName in fileNames]
        print "Found planets: "
        print planetNames
        return planetNames


    def compileYear(self):


        fileToSend = {}
        progress = self.universe.progress
        playerName = self.universe.progress.playerFactionName
        faction = progress.factions[playerName]
        # Attacking province.
        fileToSend["factionName"] = playerName
        fileToSend["pwnedPlanets"] = faction.pwnedPlanets

        saveFile = progress.saveDir + playerName +self.year + ".yer"
        pickle.dump(self.progressDict, open(saveFile, 'wb'))


    def loadYear(self, fileName):

        info = pickle.load(open(fileName, 'rb'))

        progress = self.universe.progress
        factionName = info["factionName"]
        progress.factions[factionName]["pwnedPlanets"]

    def saveCampaign(self):

