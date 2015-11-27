__author__ = 'cos'

import os
from fife.extensions import pychan
from universeUI import GalaxyUI
from huds import Widget

from dialogs import InfoDialog

class SelectPlanet(Widget):
    '''
    Opens a menu to select planets for dropship movement.
    '''

    def __init__(self, universe, selectablePlanets = None):

        super(SelectPlanet, self).__init__()

        self.selectablePlanets = selectablePlanets
        self.universe = universe
        self.widget = pychan.loadXML('gui/selectPlanet.xml')
        renderBackend = self.universe._engine.getRenderBackend()
        self.widget.min_size = renderBackend.getScreenWidth(), renderBackend.getScreenHeight()
        self.currentPlanet = self.universe.selectedPlanet.name

        self.selectedPlanet = None

        self.selectedPlanetLabel = self.widget.findChildByName("selectedPlanet")
        self.galaxyUI = GalaxyUI(self.universe, self, clickAction=self.selectPlanet)



    def activateOwnPlanets(self):
        planetList = self.universe.faction.pwnedPlanets

        self.selectablePlanets += planetList
        self.selectablePlanets = list(set(self.selectablePlanets)) # Removes duplicates.
        self.markSelectables()


    def markSelectables(self):
        '''
        Marks the planets in self.selectablePlanets.
        :return:
        '''
        for planet in self.selectablePlanets:
            self.galaxyUI.markPlanet(planet, self.galaxyUI._SELECTABLE)

        # Mark current planet as special.
        self.galaxyUI.markPlanet(self.currentPlanet, self.galaxyUI._SPECIAL)


    def selectPlanet(self, planetName):
        '''
        Handles the drawing of the planets.
        :return:
        '''

        if planetName not in self.selectablePlanets:
            InfoDialog(message="Planet not reachable.").start()
            return

        if planetName == self.currentPlanet:
            InfoDialog(message="Current planet can't be selected.").start()
            return

        if self.selectedPlanet:
            ## Unselect  the planet.
            self.galaxyUI.markPlanet(self.selectedPlanet, self.galaxyUI._SELECTABLE)

        self.selectedPlanet = planetName
        self.galaxyUI.markPlanet(self.selectedPlanet, self.galaxyUI._SELECT)


    def execute(self):
        self.markSelectables()
        if self.widget.execute({'OkButton': True, 'cancelButton' : False}):
            return self.selectedPlanet
        else:
            return None