__author__ = 'cos'


from progress import Progress
import cPickle as pickle
import os
from faction import Faction

from fife.extensions import pychan

import Tkinter, tkFileDialog



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
        self.paused = False # Tells if it is waiting a response to be loaded.

        if fileName:
            self.loadCampaign(fileName)


    def createCampaign(self):
        '''
        Opens the createCampaign dialog
        :return:
        '''
        dialog = pychan.loadXML("gui/dialogs/createCampaign.xml")
        factionList = ["Human", "Tauran"]
        dialog.distributeInitialData({"factionList" : factionList})

        def okCallback(dialog=dialog):
            campaignName, playerName, playerFaction = dialog.collectData('campaignNameText', 'playerNameText', 'factionList')
            info = {"playerName" : playerName,
                    "campaignName" : campaignName,
                    "playerFaction" : factionList[playerFaction]}
            # self.createInvitation(info)
            pickle.dump(info, open("saves/" + campaignName +".inv" , 'wb'))
            dialog.hide()
            ## TODO: Show explanation.

        dialog.mapEvents({'OkButton' : okCallback})
        dialog.show()

    # def createInvitation(self, info):
    #     '''
    #     Creates invitation file
    #     :param info:
    #     :return:
    #     '''
    #     print "CreateInvitation called with argument:"
    #     print info
    # 
    #     pickle.dump(info, open("saves/invitation.inv" , 'wb'))
        


    def joinGame(self):
        '''
        Loads an invitation and creates a proper campaign.
        :return:
        '''

        # Ask for file to load:
        root = Tkinter.Tk()
        file = tkFileDialog.askopenfile(parent=root,mode='rb',
                                        title='Select *.inv or *.rsp file',
                                        initialdir="saves",
                                        filetypes=[("Invite", ("*.inv", "*.rsp"))])
        info = None
        if file != None:
            info = pickle.load(file)
            file.close()

        root.destroy()



        if not "LocalPlayer" in info.keys():

            dialog = pychan.loadXML("gui/dialogs/createCampaign.xml")
            factionList = ["Human", "Tauran"]
            factionList.remove(info["playerFaction"])

            dialog.distributeInitialData({"factionList" : factionList,
                                          "campaignNameText" : info["campaignName"]})

            campaignInfo = { "RemotePlayer" : info}

            def okCallback(dialog=dialog, campaignInfo=campaignInfo):
                campaignName, playerName, playerFaction = dialog.collectData('campaignNameText', 'playerNameText', 'factionList')
                info = {"playerName" : playerName,
                        "campaignName" : campaignName,
                        "playerFaction" : factionList[playerFaction]}
                campaignInfo["LocalPlayer"] = info
                dialog.hide()

                # Create response:
                response = {"LocalPlayer" : campaignInfo["RemotePlayer"],
                            "RemotePlayer" : campaignInfo["LocalPlayer"]}
                pickle.dump(response, open("saves/"+ campaignName +".rsp", 'wb'))
                self.newCampaign(campaignInfo)
                self.universe.newGame(self)

            dialog.mapEvents({'OkButton' : okCallback})
            dialog.show()

        elif len(info) == 2:
            self.newCampaign(info)
            self.universe.newGame(self)




    def newCampaign(self, campaignInfo= None):

        if not campaignInfo:
            ## Ask for the name of the campaign:
            self.name = "ForeverWar"
            mainPlayer = "Me"
            mainFaction = "Human"

            otherPlayer = "You"
            otherFaction = "Tauran"
            self.playerNames = [mainPlayer, otherPlayer]
            self.factionNames = [mainFaction, otherFaction]
        else:
            localPlayerInfo = campaignInfo["LocalPlayer"]
            self.name = localPlayerInfo["campaignName"]
            self.playerNames = [localPlayerInfo["playerName"]]
            self.factionNames = [localPlayerInfo["playerFaction"]]
            remotePlayerInfo = campaignInfo["RemotePlayer"]
            self.playerNames.append(remotePlayerInfo["playerName"])
            self.factionNames.append(localPlayerInfo["playerFaction"])


            mainFaction = self.factionNames[0]
            otherFaction = self.factionNames[1]
            mainPlayer = self.playerNames[0]
            otherPlayer = self.playerNames[1]

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
        fileToSend["year"] = self.year
        fileToSend["turn"] = self.turn
        fileToSend["AttackingProvince"] = ""

        saveFile = progress.saveDir + playerFactionName + str(self.year) + ".yer"
        pickle.dump(fileToSend, open(saveFile, 'wb'))


    def loadYear(self, fileName=None):

        if not fileName:
            root = Tkinter.Tk()
            fileName = tkFileDialog.askopenfilename(parent=root,
                                        title='Select *.yer or *.trn file',
                                        initialdir="saves",
                                        filetypes=[("Turn", ("*.trn", "*.yer"))])
            root.destroy()

        info = pickle.load(open(fileName, 'rb'))

        progress = self.universe.progress

        ## Verify packet
        factionName = info["factionName"]
        year = info["year"]
        turn = info["turn"]

        packetOK = True

        if year!= self.year:
            packetOK = False
        if turn != self.turn:
            packetOK = False
        if factionName != self.enemy.factionName:
            packetOK = False

        if not packetOK:
            print "Packet invalid!"
            return

        self.enemy.pwnedPlanets  = info["pwnedPlanets"]
        ## TODO: Handle the attacking provinces
        self.year += 1

        self.paused = False

        self.universe.gui.updateUI()


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
                         "name" : self.name,
                         "paused" : self.paused}

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
        self.paused = campaignDict["paused"]

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