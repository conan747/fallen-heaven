__author__ = 'cos'



from fife import fife
import tactic_world
from agents.hero import Hero
from agents.girl import Girl
from agents.cloud import Cloud
from agents.unit import *
from agents.building import *
from scene import Scene
from fife.extensions.fife_settings import Setting

from gui.huds import TacticalHUD
from combat import Trajectory

from fife.extensions.savers import saveMapFile



_MODE_DEFAULT, _MODE_ATTACK, _MODE_DROPSHIP = xrange(3)

##  TODO: Make a Scene class that will be the parent of strategic scene and tactic scene.

class StrategicScene(Scene):
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
        super(StrategicScene, self).__init__(world, engine)

        ## Added by Jon:
        self.currentTurn = True
        self.turnCount = 0


    def reset(self):
        ### TODO This should be fixed!!!
        # self.instance_to_agent = {}
        pass

    def initAgents(self):
        """
        Setup agents.

        For this techdemo we have a very simple 'active things on the map' model,
        which is called agents. All rio maps will have a separate layer for them.

        Note that we keep a mapping from map instances (C++ model of stuff on the map)
        to the python agents for later reference.
        """
        super(StrategicScene, self).initAgents()
        ## Add the faction selection part.


    def addBuilding(self, building):
        '''
        Adds the building to the map.
        :param building:
        :return:
        '''
        building.setFootprint()
