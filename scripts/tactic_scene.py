__author__ = 'cos'



from fife import fife
import tactic_world
from agents.hero import Hero
from agents.girl import Girl
from agents.cloud import Cloud
from agents.unit import *
from scene import Scene
from fife.extensions.fife_settings import Setting

from gui.huds import TacticalHUD
from combat import Trajectory

from fife.extensions.savers import saveMapFile



_MODE_DEFAULT, _MODE_ATTACK, _MODE_DROPSHIP = xrange(3)


class TacticScene(Scene):
    """
    Master game scene.  Keeps track of all game objects.

    This is the meat and potatoes of the game.  This class takes care of the scene graph,
    updating objects, destroying objects, collision detection, etc etc.
    """

    def __init__(self, world, engine):
        """
        @param world: A reference to the master instance of the World class
        @type world: L{World}
        @param engine: A reference to the FIFE engine
        @type engine: L{fife.Engine}
        @param objectLayer: The layer that all objects exist on
        @type objectLayer: L{fife.Layer}
        """
        super(TacticScene, self).__init__(world, engine)

        ## Added by Jon:
        self.currentTurn = world.factions.keys()[0]
        self._objectsToDelete = list()

    def load(self, filename):
        super(TacticScene, self).load(filename)

        ## Start cellRenderer to show instance paths:
        [self.cellRenderer.addPathVisual(instance.agent) for instance in self.instance_to_agent.values()]
        self.cellRenderer.setEnabledPathVisual(True)
        self.cellRenderer.setEnabled(True)

        # Setup factionUnits
        for factionName in self._world.factions.keys():
            self.factionUnits[factionName] = []
            for instanceID in self.instance_to_agent.keys():
                agent = self.instance_to_agent[instanceID]
                if agent.properties["faction"] == factionName:
                    self.factionUnits[factionName].append(instanceID)



    def resetAPs(self):
        '''
        Resets the AP points of all the units to its maximum.
        '''
        for unitID in self.factionUnits[self.currentTurn]:
            print "Reseting: ", unitID
            unit = self.instance_to_agent[unitID]
            unit.resetAP()

    def nextTurn(self):
        '''
        Skips to the next turn
        '''
        if self._world.factions.keys()[0] == self.currentTurn:
            self.currentTurn = self._world.factions.keys()[1]
        else:
            self.currentTurn = self._world.factions.keys()[0]
        self._world.selectUnit(None)
        self.resetAPs()
        self._world.setMode(_MODE_DEFAULT)
        ## TO-DO: add a message stating who's turn it is.
        # print self.instance_to_agent
        # for key in self.instance_to_agent.keys():
        #     instance = self.instance_to_agent[key]
        #     instance.runTurn()


    def applyDamage(self, location, damage):
        '''
        Deals damage to a specific location (and all the units within).
        :param location: Place where the damage is applied in the map.
        :param damage: Ammount of damage dealt
        :return:
        '''
        targetIDs = self.getInstacesInTile(location)
        for unitID in targetIDs:
            if unitID in self.instance_to_agent.keys():
                self.instance_to_agent[unitID].getDamage(damage)

    def unitDied(self, unitID):
        '''
        Process the destruction of a unit
        :param unitID: ID of the destroyed unit
        :return:
        '''

        if unitID in self.instance_to_agent.keys():
            unit = self.instance_to_agent[unitID]
            self.instance_to_agent.__delitem__(unitID)
            unit.agent.removeActionListener(unit)
            self.cellRenderer.removePathVisual(unit.agent)

            self.agentLayer.deleteInstance(unit.agent)
            unit.agent = None
        for factionName in self.factionUnits.keys():
            if unitID in self.factionUnits[factionName]:
                self.factionUnits[factionName].remove(unitID)
                return

        print "Could not delete instance: " , unitID


    def reset(self):
        ### TODO This should be fixed!!!
        self.instance_to_agent = {}

