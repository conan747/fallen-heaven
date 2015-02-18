__author__ = 'cos'

# import scripts.universe
import os
from fife.extensions import pychan

from dialogs import InfoDialog

class SelectPlanet(object):
    '''
    Opens a menu to select planets for dropship movement and missile attacks.
    '''

    def __init__(self, universe):

        self.universe = universe
        self.gui = pychan.loadXML('gui/selectPlanet.xml')
        renderBackend = self.universe._engine.getRenderBackend()
        self.gui.min_size = renderBackend.getScreenWidth(), renderBackend.getScreenHeight()

        self.selectedPlanet = None

        planetNames = self.getPlanetNames()

        planetBox = self.gui.findChild(name="planetBox")
        for name in planetNames:
            newButton = pychan.Label(name=name,
                                     text=unicode("Go to planet " + name),
                                     is_focusable=True,
                                     base_color=(255,0,0,200),
                                     foreground_color=(0,0,0)
                                        )
            pychan.TextField
            planetBox.addChild(newButton)
            def callback(arg=name, widget=None): # Weird way of doing it. Taken from here: http://wiki.wxpython.org/Passing%20Arguments%20to%20Callbacks
                        self.selectPlanet(arg, widget)
            newButton.capture(callback, event_name="mouseClicked")


        # eventMap = {
            # 'toWar': self.universe.toWarClicked,
            # 'toCapital': self.universe.toCapitalClicked,
            # 'toPlanet': self.universe.toPlanetClicked,
            # 'OkButton': self.onOkPressed,
            # 'cancelButton' : self.onCancelPressed
        # }
        # self.gui.mapEvents(eventMap)
        self.selectedPlanetLabel = self.gui.findChildByName("selectedPlanet")
        self.gui.show()




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

    def show(self):
        self.gui.show()

    def hide(self):
        self.gui.hide()

    def selectPlanet(self, planetName, widget=None):
        '''
        Handles the drawing of the planets.
        :return:
        '''
        if self.selectedPlanet:
            ## Unselect  the planet.
            planetLabel = self.gui.findChildByName(self.selectedPlanet)
            self.setHighlighting(planetLabel, False)

        self.selectedPlanet = planetName
        self.selectedPlanetLabel.text = planetName
        self.setHighlighting(widget)

    def setHighlighting(self, widget, bol=True):
        if bol:
            widget.border_size = 1
        else:
            widget.border_size = 0

    def updateUI(self):
        '''
        Will update the Universe UI information.
        :return:
        '''
        pass
        ## TODO: Handle planet owner printing.

        '''
        # Update pwned planets

        planetBox = self.gui.findChild(name="planetBox")
        planetBox.removeAllChildren()
        for name in self.universe.faction.pwnedPlanets:
            newButton = pychan.Button(name=name, text=unicode("Go to planet " + name))
            planetBox.addChild(newButton)
            def callback(arg=name): # Weird way of doing it. Taken from here: http://wiki.wxpython.org/Passing%20Arguments%20to%20Callbacks
                        self.universe.goToPlanet(arg)
            newButton.capture(callback, event_name="mouseClicked")

        separator = pychan.Spacer(planetBox)
        newButton = pychan.Button(name="test" , text="Go to war!")
        newButton.capture(self.universe.toWarClicked)
        planetBox.addChild(newButton)

        # Update year:
        yearLabel = self.gui.findChildByName("year")
        year = self.universe.campaign.year
        yearLabel.text = unicode(str(year))

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
            '''

    def execute(self):
        if self.gui.execute({'OkButton': True, 'cancelButton' : False}):
            return self.selectedPlanet
        else:
            return None