__author__ = 'cos'


import cPickle as pickle
import os
from faction import Faction
from gui.dialogs import InfoDialog

from fife.extensions import pychan

from galaxy import Galaxy

import Tkinter, tkFileDialog


class Campaign(object):
    '''
    Campaign object is the main object that holds all the information about the game.
    In principle it holds public information i.e. could be shared among players. It also contains the
    progress field scpecific for this player (private part).
    '''

    def __init__(self, universe, fileName=None):
        self.universe = universe
        self.galaxyName = None
        self.year = 0 # Strategic turn
        self.turn = 0 # Tactic turn
        self.progress = None # Player progress.
        self.name = "ForeverWar" # Name of the campaign
        self.factions = {}  # Dictionary containing "factionName" : Faction()
        self.paused = False # Tells if it is waiting a response to be loaded.
        self.saveDir = ""
        self.player2Faction = {} # Dictionary mapping the player name to the faction.

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
            campaignName, playerName, playerFaction, saveDir = dialog.collectData('campaignNameText',
                                                                                  'playerNameText',
                                                                                  'factionList',
                                                                                  'saveDir')
            if saveDir[-1] != "/":
                saveDir += "/" + campaignName + "/"
            else:
                saveDir += campaignName + "/"

            info = {"playerName" : playerName,
                    "campaignName" : campaignName,
                    "playerFaction" : factionList[playerFaction],
                    "saveDir" : saveDir}
            # self.createInvitation(info)
            if not saveDir:
                saveDir = "saves"

            def make_tree(path):
                if not os.path.isdir(path):
                    parent = os.path.dirname(path)
                    make_tree(parent)
                    if not os.path.isdir(path):
                        os.mkdir(path)

            make_tree(saveDir)

            pickle.dump(info, open(saveDir + campaignName +".inv" , 'wb'))
            print "Chosen dir:" , saveDir
            # dialog.hide()
            print "Dialog executed"

        def saveDialogCallback(dialog=dialog):
            root = Tkinter.Tk()
            root.withdraw()
            dir = tkFileDialog.askdirectory(parent=root,
                                        title='Select saves parent directory.',
                                        initialdir="saves")
            if dir:
                children = dialog.findChildren(name="saveDir")
                for child in children:
                    child.text = os.path.abspath(dir)

        dialog.mapEvents({'OkButton' : okCallback,
                          'saveDialog': saveDialogCallback})

        result = dialog.execute({'OkButton': True, 'cancelButton' : False})
        if result:
            print "This returns true"
            info = InfoDialog('Invitation for the campaign (".inv") created! Send it to the other player so that he can join. Press ESC to go back to main menu.')
            info.start()
        else:
            print "It returned false!"
            info = InfoDialog('Campaign creatinon cancelled! Press ESC to go back to main menu.')
            info.start()


    def joinGame(self):
        '''
        Loads an invitation and creates a proper campaign.
        :return:
        '''


        # Information:
        infoDialog = InfoDialog("Load a .inv file or a .rsp file to start playing the campaign.")
        infoDialog.start()

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
                                          "campaignNameText" : info["campaignName"],
                                          'saveDir' : info["saveDir"]})

            #Block fields:
            #dialog.findChildByName("campaignNameText").setEditable(False)
            ##TODO: Add campaignNameText selection block.

            campaignInfo = { "RemotePlayer" : info}

            def okCallback(dialog=dialog, campaignInfo=campaignInfo):
                campaignName, playerName, playerFaction, saveDir = dialog.collectData('campaignNameText',
                                                                             'playerNameText',
                                                                             'factionList',
                                                                             'saveDir')

                if saveDir[-1] != "/":
                    saveDir += "/"
                info = {"playerName" : playerName,
                        "campaignName" : campaignName,
                        "playerFaction" : factionList[playerFaction],
                        "saveDir" : saveDir}

                campaignInfo["LocalPlayer"] = info
                dialog.hide()

                # Create response:
                response = {"LocalPlayer" : campaignInfo["RemotePlayer"],
                            "RemotePlayer" : campaignInfo["LocalPlayer"]}

                if not saveDir:
                    saveDir = "saves"

                def make_tree(path):
                    if not os.path.isdir(path):
                        parent = os.path.dirname(path)
                        make_tree(parent)
                        os.mkdir(path)

                make_tree(saveDir)

                pickle.dump(response, open(saveDir + campaignName +".rsp", 'wb'))
                self.newCampaign(campaignInfo)
                self.universe.newGame(self)

            def saveDialogCallback(dialog=dialog):
                root = Tkinter.Tk()
                root.withdraw()
                dir = tkFileDialog.askdirectory(parent=root,
                                            title='Select saves parent directory.',
                                            initialdir="saves")
                if dir:
                    child = dialog.findChildByName("saveDir")
                    child.text = os.path.abspath(dir) + "/" + info["campaignName"]

            dialog.mapEvents({'OkButton' : okCallback,
                          'saveDialog': saveDialogCallback})
            dialog.execute({'OkButton' : True})
            ## TODO: Add cancel button action.

            # Information:
            infoDialog = InfoDialog("Campaign properly joined! Now send the .rsp file to your opponent. You can now start playing the first turn.")
            infoDialog.start()

            self.newCampaign(campaignInfo)
            self.universe.newGame(campaign=self, giveFreebies=True)
            self.saveCampaign()

        elif len(info) == 2:
            # It seems it was a response packet.
            # Information:
            infoDialog = InfoDialog("Campaign properly joined! You can now start playing the first turn.")
            infoDialog.start()

            self.newCampaign(info)
            self.universe.newGame(campaign=self, giveFreebies=True)
            self.saveCampaign()


    def newCampaign(self, campaignInfo= None):

        if not campaignInfo:
            InfoDialog(message="Error: No campaign info. This should never happen.").execute()
            return

        localPlayerInfo = campaignInfo["LocalPlayer"]
        self.name = localPlayerInfo["campaignName"]
        self.saveDir = localPlayerInfo["saveDir"]
        if self.saveDir[-1] != "/":
            self.saveDir += "/"

        for player in ["LocalPlayer", "RemotePlayer"]: # Maybe there should be more fields?
            info = campaignInfo[player]
            self.player2Faction[info["playerName"]] = info["playerFaction"]

        myPlayer = localPlayerInfo["playerName"]
        myFaction = self.player2Faction[myPlayer]

        self.progress = Progress(self.universe, playerFactionName= myFaction, saveDir=self.saveDir)
        for factionName in self.player2Faction.values():
            self.factions[factionName] = Faction(factionName)

        self.progress.factionInfo = self.factions[myFaction].__getInfo__()
        self.progress.playerName = myPlayer

        print self.progress


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

        ## Verify packet
        factionName = info["factionName"]
        year = info["year"]
        turn = info["turn"]

        packetOK = True

        if year!= self.year:
            packetOK = False
        if turn != self.turn:
            packetOK = False
        # if factionName != self.enemy.factionName:
        #     packetOK = False

        if not packetOK:
            print "Packet invalid!"
            return

        self.factions[factionName].pwnedPlanets = info["pwnedPlanets"]
        ## TODO: Handle the attacking provinces
        self.year += 1

        self.paused = False

        self.universe.gui.updateUI()
        self.saveCampaign()

    def getEnemy(self):
        '''
        Returns the faction corresponding to the enemy
        :return:
        '''
        playerFactionName = self.progress.playerFactionName
        return [self.factions[name] for name in self.factions.keys()
                if name != playerFactionName]

    def getPlayerFaction(self):
        '''
        Returns the faction corresponding to the player
        :return:
        '''
        return self.factions[self.progress.playerFactionName]

    def saveCampaign(self):
        '''
        Saves the campaign file .cpn
        :return:
        '''

        campaignDict = { "playerName" : self.progress.playerName,
                         "year" : self.year,
                         "turn" : self.turn,
                         "player2Faction" : self.player2Faction,
                         "name" : self.name,
                         "paused" : self.paused,
                         "saveDir" : self.saveDir,
                         "galaxy" : self.galaxyName
                        }

        campaignDict["factionInfo"] = [faction.__getInfo__() for faction in self.factions.values()]

        pickle.dump(campaignDict, open("%s/%s_%s.cpn" %
                                       (self.saveDir, self.name, self.progress.playerName), 'wb'))

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
        self.galaxyName = campaignDict["galaxy"]
        self.player2Faction = campaignDict["player2Faction"]
        self.paused = campaignDict["paused"]
        if "saveDir" in campaignDict.keys():
            self.saveDir = campaignDict["saveDir"]
        else:
            self.saveDir = "saves"

        playerName = campaignDict["playerName"]
        rootFolder = os.path.dirname(fileName)
        progress = Progress(self.universe)
        progress.load(rootFolder + "/" + playerName + ".prg")
        self.progress = progress

        for factionInfo in campaignDict["factionInfo"]:
            factionName = factionInfo["name"]
            self.factions[factionName] = Faction(factionInfo=factionInfo)


###################################################
#   Progress
###################################################



class Progress(object):
    '''
    Tracks the current progress to save/restore games.
    '''


    def __init__(self, universe, playerFactionName="Human", saveDir="saves/test"):
        '''

        :return:
        '''
        self.universe = universe # Points at the universe

        self.playerFactionName = playerFactionName
        self.playerName = ""

        self.saveDir = saveDir   # Directory where the file should be saved/loaded
        self.planetInfos = {} # Dictionary containing planet name:planetInfo

        # Dictionary containing all the information. Will be saved/loaded.
        self.progressDict = {"playerFactionName" : self.playerFactionName,
                             "saveDir" : self.saveDir}


        self.waitingForResponse = False
        self.attacking = {} # list containing the "Attacking info" of the dropships of this player.
        ## Attacking will contain: {"origin": <name of the planet of origin>,
        ##                  "target": <name of the destination planet>
        ##                  "storage": <storage dictionary that this dropship has>


    def update(self):

        # Update open planet:
        if self.universe.world:
            if self.universe.world.planet:
                self.universe.world.updatePlanetAgents()
                storages = self.universe.world.getStorageDicts()
                planetDict = self.universe.world.planet.getPlanetDict()
                planetDict["storages"] = storages
                self.planetInfos[planetDict["name"]] = planetDict

        self.progressDict["planetInfos"] = self.planetInfos
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










