__author__ = 'cos'



# from fife import fife
# import tactic_world
# from agents.hero import Hero
# from agents.girl import Girl
# from agents.cloud import Cloud
# from agents.unit import *
# from fife.extensions.fife_settings import Setting
#
# from gui.huds import TacticalHUD
# from combat import Trajectory
#
# from fife.extensions.savers import saveMapFile


from scene import Scene


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
        playerFactionName = world.universe.progress.playerFactionName
        self.currentTurn = playerFactionName
        self.factionNames = [playerFactionName, "Tauran"]

    def load(self, filename):
        super(TacticScene, self).load(filename)

        ## Start cellRenderer to show instance paths:
        self.view.setVisual(self.unitManager.getAgents())

        # Setup factionUnits
        for factionName in self.factionNames:
            self.factionUnits[factionName] = []
            for agent in self.unitManager.getAgents():
                if agent.properties["faction"] == factionName:
                    self.factionUnits[factionName].append(agent.getFifeId())

        self._world.selectUnit(None)



    def resetAPs(self):
        '''
        Resets the AP points of all the units to its maximum.
        '''
        for unitID in self.factionUnits[self.currentTurn]:
            print "Reseting: ", unitID
            unit = self.unitManager.getAgent(unitID)
            unit.resetAP()

    def nextTurn(self):
        '''
        Skips to the next turn
        '''
        if self.factionNames[0] == self.currentTurn:
            self.currentTurn = self.factionNames[1]
        else:
            self.currentTurn = self.factionNames[0]
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
        targetIDs = self._world.getInstancesAt(location)
        for unitID in targetIDs:
            agent = self.unitManager.getAgent(unitID)
            print "Dealt %s damage to %s" % (damage, agent.instance.getId())
            agent.getDamage(damage)



    def unitDied(self, unitID):
        '''
        Process the destruction of a unit
        :param unitID: ID of the destroyed unit
        :return:
        '''

        self._world.view.removePathVisual(self.unitManager.getAgent(unitID).instance)

        self.unitManager.removeInstance(unitID)

        for factionName in self.factionUnits.keys():
            if unitID in self.factionUnits[factionName]:
                self.factionUnits[factionName].remove(unitID)
                return


        print "Could not delete instance: " , unitID


    def reset(self):
        ### TODO This should be fixed!!!
        pass

