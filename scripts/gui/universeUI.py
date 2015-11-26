__author__ = 'cos'

# import scripts.universe
import os
from fife.extensions import pychan

from dialogs import InfoDialog

class UniverseUI(object):
    '''
    Handles the UI part of the Universe view. Displays the planet map, information.
    '''

    _planetInfoFile = "gui/planets/planetInfo.txt"

    def __init__(self, universe):

        self.universe = universe
        self.gui = pychan.loadXML('gui/universe_screen.xml')
        self.gui.min_size = self.universe._engine.getRenderBackend().getScreenWidth(), self.universe._engine.getRenderBackend().getScreenHeight()

        planetNames = self.getPlanetNames()

        # self.createSimpleButtons(planetNames)
        self.createPlanetIcons(planetNames)
        eventMap = {
            # 'toWar': self.universe.toWarClicked,
            # 'toCapital': self.universe.toCapitalClicked,
            # 'toPlanet': self.universe.toPlanetClicked,
            'endTurn': self.universe.endTurn
        }
        self.gui.mapEvents(eventMap)

    def createPlanetIcons(self, planetNames):
        planetBox = self.gui.findChild(name="planetBox")
        imagePattern="gui/planets/%s.png"

        #Load planet info from file
        with open(self._planetInfoFile, 'r') as planetInfoFile:
            planetInfo = planetInfoFile.readlines()

        planetCoords = {}
        for line in planetInfo:
            info = line.split()
            planetCoords[info[0]] = info[1:]

        for name in planetNames:
            print "Loading " , imagePattern % name
            coords = planetCoords[name]
            coords = [int(x) for x in coords]
            newIcon = pychan.Icon(parent=planetBox,
                                  name=name,
                                  image=imagePattern % name,
                                  base_color=(255,0,0),
                                  position=coords)
            planetBox.addChild(newIcon)

    def createSimpleButtons(self,  planetNames):
        planetBox = self.gui.findChild(name="planetBox")
        for name in planetNames:

            newButton = pychan.Button(name=name, text=unicode("Go to planet " + name), parent=planetBox)
            planetBox.addChild(newButton)
            def callback(arg=name): # Weird way of doing it. Taken from here: http://wiki.wxpython.org/Passing%20Arguments%20to%20Callbacks
                        self.universe.goToPlanet(arg)
            newButton.capture(callback, event_name="mouseClicked")


    def getPlanetNames(self):
        '''
        Gets a list of planet names from the map directory
        :return:
        '''
        fileNames = os.listdir("maps")
        planetNames = [fileName.split(".xml")[0] for fileName in fileNames
                       if ".xml" in fileName]
        print "Found planets: "
        print planetNames
        return planetNames

    def show(self):
        self.gui.show()

    def hide(self):
        self.gui.hide()

    def updateUI(self):
        '''
        Will update the Universe UI information.
        :return:
        '''

        # Update pwned planets

        planetBox = self.gui.findChild(name="planetBox")
        # planetBox.removeAllChildren()
        for name in self.universe.faction.pwnedPlanets:
            planetButton = planetBox.findChild(name=name)
            def callback(arg=name): # Weird way of doing it. Taken from here: http://wiki.wxpython.org/Passing%20Arguments%20to%20Callbacks
                        self.universe.goToPlanet(arg)
            planetButton.capture(callback, event_name="mouseClicked")
            planetButton._setBorderSize(2)

        separator = pychan.Spacer(planetBox)
        newButton = pychan.Button(name="test", text="Go to war!")
        newButton.capture(self.universe.toWarClicked)
        planetBox.addChild(newButton)

        # self.createPlanetIcons(self.universe.faction.pwnedPlanets)

        # Update year:
        yearLabel = self.gui.findChildByName("year")
        year = self.universe.campaign.year
        yearLabel.text = unicode(str(year))

        #Update faction+ player name
        factionName = self.universe.faction.name
        playerName = self.universe.progress.playerName
        factionLabel = self.gui.findChildByName("faction")
        factionLabel.text = unicode(factionName)
        playerLabel = self.gui.findChildByName("playerName")
        playerLabel.text = unicode(playerName)

        self.handlePaused()
        self.gui.adaptLayout()


    def handlePaused(self):

        if self.universe.campaign.paused:
            if not self.gui.findChildByName("loadTurn"):
                buttonBox = self.gui.findChildByName("buttonBox")
                loadTurnButton = pychan.Button(parent=buttonBox,
                                               name="loadTurn",
                                               text="Load next turn")
                buttonBox.addChild(loadTurnButton)
                loadTurnButton.capture(self.universe.campaign.loadYear)

            endTurnButton = self.gui.findChildByName("endTurn")
            endTurnButton.hide()
            loadTurnButton = self.gui.findChildByName("loadTurn")
            loadTurnButton.show()
            # self.gui.adaptLayout()

            dialog = InfoDialog(message="Send the automatically generated .yer file and wait for the response.",
                            title= "Game paused.")
            dialog.show()

        else:
            loadTurnButton = self.gui.findChildByName("loadTurn")
            if loadTurnButton:
                loadTurnButton.hide()
            endTurnButton = self.gui.findChildByName("endTurn")
            endTurnButton.show()