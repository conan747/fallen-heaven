__author__ = 'cos'

# import scripts.universe
import os
from fife.extensions import pychan


class UniverseUI(object):
    '''
    Handles the UI part of the Universe view. Displays the planet map, information.
    '''

    def __init__(self, universe):

        self.universe = universe
        self.gui = pychan.loadXML('gui/universe_screen.xml')
        self.gui.min_size = self.universe._engine.getRenderBackend().getScreenWidth(), self.universe._engine.getRenderBackend().getScreenHeight()

        planetNames = self.getPlanetNames()

        planetBox = self.gui.findChild(name="planetBox")
        for name in planetNames:
            newButton = pychan.Button(name=name, text=unicode("Go to planet " + name))
            planetBox.addChild(newButton)
            def callback(arg=name): # Weird way of doing it. Taken from here: http://wiki.wxpython.org/Passing%20Arguments%20to%20Callbacks
                        self.universe.goToPlanet(arg)
            newButton.capture(callback, event_name="mouseClicked")


        eventMap = {
            # 'toWar': self.universe.toWarClicked,
            # 'toCapital': self.universe.toCapitalClicked,
            # 'toPlanet': self.universe.toPlanetClicked,
            'endTurn': self.universe.endTurn
        }
        self.gui.mapEvents(eventMap)



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

    def updateUI(self):
        '''
        Will update the Universe UI information.
        :return:
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

        planetBox.adaptLayout()