__author__ = 'cos'


from progress import Progress
import cPickle as pickle
import os
from faction import Faction



class Enemy(object):
    '''
    Holds the information of the other player.
    '''

    def __init__(self):

        self.name = ""
        self.factionName = ""
        self.pwnedPlanets = []


class Campaign(object):
    '''
    Campaign object deals with the information exchange between players.
    '''

    def __init__(self, universe, fileName=None):
        self.universe = universe
        self.planetList = self.getPlanetNames()
        self.year = 0 # Strategic turn
        self.turn = 0 # Tactic turn
        self.progress = None # Player progress.
        self.name = "ForeverWar" # Name of the campaign
        self.factionNames = []

        if fileName:
            self.loadCampaign(fileName)


    def newCampaign(self):

        ## TODO: Make a gui to retrieve this information
        ## Ask for the name of the campaign:
        self.name = "ForeverWar"
        mainPlayer = "Me"
        mainFaction = "Human"

        otherPlayer = "You"
        otherFaction = "Tauran"
        self.playerNames = [mainPlayer, otherPlayer]
        self.factionNames = [mainFaction, otherFaction]

        progress = Progress(self.universe)
        progress.playerFactionName = mainFaction
        faction = Faction(mainFaction)
        progress.factionInfo = faction.__getInfo__()
        progress.playerName = mainPlayer
        self.progress = progress
        ## Assign initial pwned planets:
        self.progress.factionInfo["pwnedPlanets"] = ["firstCapital"]

        ## Create the enemy information:
        self.enemy = Enemy()
        self.enemy.name = otherPlayer
        self.enemy.factionName = otherFaction
        self.enemy.pwnedPlanets = ["enemyPlanet"]


        print self.progress


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
        playerFactionName = self.universe.progress.playerFactionName
        faction = progress.faction
        # Attacking province.
        fileToSend["factionName"] = playerFactionName
        fileToSend["pwnedPlanets"] = faction.pwnedPlanets

        saveFile = progress.saveDir + playerFactionName +self.year + ".yer"
        pickle.dump(self.progressDict, open(saveFile, 'wb'))


    def loadYear(self, fileName):

        info = pickle.load(open(fileName, 'rb'))

        progress = self.universe.progress
        factionName = info["factionName"]
        info["pwnedPlanets"] = progress.faction["pwnedPlanets"]

    def saveCampaign(self):
        '''
        Saves the campaign file .cpn
        :return:
        '''


        campaignDict = { "playerName" : self.progress.playerName,
                         "year" : self.year,
                         "turn" : self.turn,
                         "planetList" : self.planetList,
                         "factionNames" : self.factionNames,
                         "name" : self.name}

        enemyInfo = {}
        for atr in dir(self.enemy):
            if not atr.startswith("__"):
                enemyInfo[atr] = getattr(self.enemy, atr)
        campaignDict["enemyInfo"] = enemyInfo

        pickle.dump(campaignDict, open("saves/test/" + self.name + ".cpn", 'wb'))

        self.progress.save()

    def loadCampaign(self, fileName):
        '''
        Loads campaign file.
        :param fileName:
        :return:
        '''

        campaignDict = pickle.load(open(fileName, 'rb'))
        self.name = campaignDict["name"]
        self.year = campaignDict["year"]
        self.turn = campaignDict["turn"]
        self.planetList = campaignDict["planetList"]
        self.factionNames = campaignDict["factionNames"]

        playerName = campaignDict["playerName"]
        rootFolder = os.path.dirname(fileName)
        progress = Progress(self.universe)
        progress.load(rootFolder + "/" + playerName + ".prg")
        self.progress = progress

        self.enemy = Enemy()
        enemyInfo = campaignDict["enemyInfo"]
        [setattr(self.enemy, key, enemyInfo[key]) for key in enemyInfo.keys()]


        # TODO: MAke this variable.
        # return progress