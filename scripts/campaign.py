__author__ = 'cos'


import cPickle as pickle
import os
from faction import Faction
from gui.dialogs import InfoDialog

from fife.extensions import pychan

from galaxy import Galaxy

import Tkinter, tkFileDialog



class Enemy(object):
    '''
    Holds the information of the other player.
    '''

    def __init__(self):

        self.name = ""
        self.factionName = ""
        self.pwnedPlanets = []

    def __getInfo__(self):
        enemyInfo = {}
        for atr in dir(self):
            if not atr.startswith("__"):
                enemyInfo[atr] = getattr(self, atr)
        return enemyInfo


class Campaign(object):
    '''
    Campaign object deals with the information exchange between players.
    '''

    def __init__(self, universe, fileName=None):
        self.universe = universe
        self.galaxyName = None
        ## TODO: Change this, it should depend on the galaxy name.
        galaxy = Galaxy()
        self.planetList = galaxy.getPlanetNames()
        self.year = 0 # Strategic turn
        self.turn = 0 # Tactic turn
        self.progress = None # Player progress.
        self.name = "ForeverWar" # Name of the campaign
        self.factionNames = []
        self.paused = False # Tells if it is waiting a response to be loaded.
        self.saveDir = ""

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
            ##TODO: Add faction selection block.

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
            self.saveDir = localPlayerInfo["saveDir"]
            if self.saveDir[-1] != "/":
                self.saveDir += "/"

            mainFaction = self.factionNames[0]
            otherFaction = self.factionNames[1]
            mainPlayer = self.playerNames[0]
            otherPlayer = self.playerNames[1]

        progress = Progress(self.universe, playerFactionName= mainFaction, saveDir=self.saveDir)
        faction = Faction(localPlayerInfo["playerFaction"])
        progress.factionInfo = faction.__getInfo__()
        progress.playerName = mainPlayer
        self.progress = progress

        ## Create the enemy information:
        self.enemy = Enemy()
        self.enemy.name = otherPlayer
        self.enemy.factionName = otherFaction

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
        self.saveCampaign()


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
                         "paused" : self.paused,
                         "saveDir" : self.saveDir
                        }

        campaignDict["enemyInfo"] = self.enemy.__getInfo__()

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
        self.planetList = campaignDict["planetList"]
        self.factionNames = campaignDict["factionNames"]
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

        self.enemy = Enemy()
        enemyInfo = campaignDict["enemyInfo"]
        [setattr(self.enemy, key, enemyInfo[key]) for key in enemyInfo.keys()]


        # TODO: MAke this variable.
        # return progress


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
        self.saveDir = saveDir   # Directory where the file should be saved/loaded
        self.allPlanets = {} # Dictionary containing planet name:planetInfo
        self.factionInfo = None # Dictionary containing faction factionInfo.

        # Dictionary containing all the information. Will be saved/loaded.
        self.progressDict = {"playerFactionName" : self.playerFactionName,
                             "saveDir" : self.saveDir}

        self.playerName = ""
        self.waitingForResponse = False
        self.attacking = {} # list containing the "Attacking info" of the dropships of this player.
        ## Attacking will contain: {"origin": <name of the planet of origin>,
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
                self.universe.world.updatePlanetAgents()
                storages = self.universe.world.getStorageDicts()
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










