__author__ = 'cos'


from progress import Progress
import cPickle as pickle
import os
from faction import Faction


class Campaign(object):
    '''
    Campaign object deals with the information exchange between players.
    '''

    def __init__(self, universe, fileName=None):
        self.universe = universe
        self.planetList = self.getPlanetNames()
        self.year = 0 # Strategic turn
        self.turn = 0 # Tactic turn
        self.players = {} # Dictionary containing {playerName : PlayerProgress}
        self.name = "ForeverWar"

        if fileName:
            self.loadCampaign(fileName)


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

        # for playerName in self.players.keys():
        #     self.players[playerName].playerName = playerName
        #     self.players[playerName].save()

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
        '''
        Saves the campaign file .cpn
        :return:
        '''
        playerNames = self.players.keys()

        campaignDict = { "playerNames" : playerNames,
                         "year" : self.year,
                         "turn" : self.turn,
                         "planetList" : self.planetList}

        pickle.dump(campaignDict, open("saves/test/" + self.name + ".cpn" , 'wb'))

        for prog in self.players.values():
            prog.save()

    def loadCampaign(self, fileName):
        '''
        Loads campaign file.
        :param fileName:
        :return:
        '''

        campaignDict = pickle.load(open(fileName, 'rb'))
        self.year = campaignDict["year"]
        self.turn = campaignDict["turn"]
        self.planetList = campaignDict["planetList"]

        rootFolder = os.path.dirname(fileName)
        for playerName in campaignDict["playerNames"]:
            progress = Progress(self.universe)
            self.players[playerName] = progress.load(rootFolder + "/" + playerName + ".prg")

        # TODO: MAke this variable.
        return players["Me"]