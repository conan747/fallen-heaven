__author__ = 'cos'

# import scripts.universe
import os
from fife.extensions import pychan

from dialogs import InfoDialog
from huds import Widget



class GalaxyUI(Widget):
    '''
    Holds the UI widget showing the planets. It can be extended to form planet selection interfaces.
    '''

    _UNSELECT, _SELECTABLE, _SELECT, _NOTPOSSIBLE, _SPECIAL = xrange(0, 5)
    _planetInfoFile = "gui/planets/planetInfo.txt"

    def __init__(self, universe, parentUI=None, clickAction=None, doubleClickAction=None):
        
        super(GalaxyUI, self).__init__()
        self.universe = universe
        self.galaxy = self.universe.galaxy
        self.parentUI = parentUI
        self.widget = pychan.loadXML('gui/galaxyUI.xml')
        if self.parentUI:
            parent = self.parentUI.widget.findChildByName("galaxyUI")
            if parent:
                self.widget.parent = parent
                parent.addChild(self.widget)

        planetNames = self.galaxy.getPlanetNames()
        self.createPlanetIcons(planetNames)

        self.timer = self.universe._engine.getTimeManager()
        self.__doubleClickTime = 500 # milliseconds ##TODO: put this in settings.
        self.lastClickTime = 0

        self.clickAction = clickAction
        self.doubleClickAction = doubleClickAction



    def createPlanetIcons(self, planetNames):
        planetBox = self.widget.findChildByName("planetBox")
        imagePattern="gui/planets/%s.png"

        #Load planet info from file
        with open(self._planetInfoFile, 'r') as planetInfoFile:
            planetInfo = planetInfoFile.readlines()

        planetCoords = {}
        for line in planetInfo:
            info = line.split()
            planetCoords[info[0]] = info[1:3]

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

            def clicked(planetName=name):
                self.planetClicked(planetName)
            newIcon.capture(clicked, event_name="mouseClicked")


    def isDoubleClick(self):
        '''
        Returns if the click is considered a double click or not.
        :return: Boolean
        '''
        nowTime = self.timer.getTime()
        if (nowTime - self.lastClickTime) < self.__doubleClickTime:
            self.lastClickTime = nowTime
            return True
        self.lastClickTime = nowTime
        return False


    def planetClicked(self, planetName):
        if self.isDoubleClick():
            if self.doubleClickAction:
                self.doubleClickAction(planetName)
        else:
            if self.clickAction:
                self.clickAction(planetName)

    def markPlanet(self, planetName, mode=0):
        widget = self.widget.findChildByName(planetName)
        if mode == self._UNSELECT:
            widget.border_size = 0
            return

        borderColor = None
        if mode == self._SELECTABLE:
            borderColor = (100, 100, 100, 128)
        elif mode == self._SELECT:
            borderColor = (0, 255, 0, 128)
        elif mode == self._NOTPOSSIBLE:
            borderColor = (255, 0, 0, 128)
        elif mode == self._SPECIAL:
            borderColor = (0, 0, 255, 128)

        widget.base_color = borderColor
        widget.border_size = 2

    def unselectAllPlanets(self):
        planetNames = self.galaxy.getPlanetNames()
        for planet in planetNames:
            self.markPlanet(planet, self._UNSELECT)


class UniverseUI(Widget):
    '''
    Handles the UI part of the Universe view. Displays the planet map, information.
    '''


    def __init__(self, universe):

        self.universe = universe
        self.widget = pychan.loadXML('gui/universe_screen.xml')
        renderBackend = self.universe._engine.getRenderBackend()
        self.widget.min_size = renderBackend.getScreenWidth(), renderBackend.getScreenHeight()

        self.galaxyUI = GalaxyUI(self.universe, parentUI=self,
                                 clickAction=self.showPlanetInfo,
                                 doubleClickAction=self.goToPlanet)
        eventMap = {
            'endTurn': self.universe.endTurn
        }
        self.widget.mapEvents(eventMap)


    def updateUI(self):
        '''
        Will update the Universe UI information.
        :return:
        '''

        # Update pwned planets
        planetBox = self.widget.findChild(name="planetBox")
        # planetBox.removeAllChildren()
        self.galaxyUI.unselectAllPlanets()
        for name in self.universe.faction.pwnedPlanets:
            self.galaxyUI.markPlanet(name, self.galaxyUI._SELECTABLE)
            self.galaxyUI.doubleClickAction = self.goToPlanet

        separator = pychan.Spacer(planetBox)
        newButton = pychan.Button(name="test", text="Go to war!")
        newButton.capture(self.universe.toWarClicked)
        planetBox.addChild(newButton)

        # Update year:
        yearLabel = self.widget.findChildByName("year")
        year = self.universe.campaign.year
        yearLabel.text = unicode(str(year))

        #Update faction+ player name
        factionName = self.universe.faction.name
        playerName = self.universe.progress.playerName
        factionLabel = self.widget.findChildByName("faction")
        factionLabel.text = unicode(factionName)
        playerLabel = self.widget.findChildByName("playerName")
        playerLabel.text = unicode(playerName)

        self.handlePaused()
        self.widget.adaptLayout()

    def showPlanetInfo(self, planetName):
        '''
        This gets executed when a single click is performed.
        :param planetName: planet where there was a click
        :return:
        '''
        infoLabel = self.widget.findChildByName("InfoLabel")
        if planetName in self.universe.faction.pwnedPlanets:
            infoLabel.text = "Clicked: %s \n Owned by player." % planetName
            self.galaxyUI.markPlanet(planetName, self.galaxyUI._SELECT)
        else:
            infoLabel.text = "Clicked: %s \n Not owned by player." % planetName



    def goToPlanet(self, planetName):
        '''
        Checks if we can actually go to that planet.
        :param planetName: Name of the planet
        :return:
        '''
        if planetName in self.universe.faction.pwnedPlanets:
            self.universe.goToPlanet(planetName)
        else:
            dialog = InfoDialog(message="You can't visit that planet because you don't own it.",
                            title= "Error visiting planet")
            dialog.start()


    def handlePaused(self):

        if self.universe.campaign.paused:
            if not self.widget.findChildByName("loadTurn"):
                buttonBox = self.widget.findChildByName("buttonBox")
                loadTurnButton = pychan.Button(parent=buttonBox,
                                               name="loadTurn",
                                               text="Load next turn")
                buttonBox.addChild(loadTurnButton)
                loadTurnButton.capture(self.universe.campaign.loadYear)

            endTurnButton = self.widget.findChildByName("endTurn")
            endTurnButton.hide()
            loadTurnButton = self.widget.findChildByName("loadTurn")
            loadTurnButton.show()
            # self.widget.adaptLayout()

            dialog = InfoDialog(message="Send the automatically generated .yer file and wait for the response.",
                            title= "Game paused.")
            dialog.show()

        else:
            loadTurnButton = self.widget.findChildByName("loadTurn")
            if loadTurnButton:
                loadTurnButton.hide()
            endTurnButton = self.widget.findChildByName("endTurn")
            endTurnButton.show()