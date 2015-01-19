__author__ = 'cos'



from fife import fife
import tactic_world
from agents.hero import Hero
from agents.girl import Girl
from agents.cloud import Cloud
from agents.unit import *
from agents.beekeeper import Beekeeper
from agents.agent import create_anonymous_agents
from fife.extensions.fife_settings import Setting

from gui.huds import TacticalHUD
from combat import Trajectory

from fife.extensions.savers import saveMapFile



_MODE_DEFAULT, _MODE_ATTACK, _MODE_DROPSHIP = xrange(3)


class TacticScene(object):
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
        self.engine = engine
        self._world = world
        self._model = engine.getModel()
        self.agentLayer = None

        self._objectstodelete = list()

        self._time = 0
        self._timedelta = 0
        self._lasttime = 0

        self._music = None


        ## Added by Jon:
        self.factionUnits = {}      ## This will hold the units for each faction.
        self.currentTurn = True
        self._player1 = True
        self._player2 = False
        self._objectsToDelete = list()


    def destroyScene(self):
        """
        Removes all objects from the scene and deletes them from the layer.
        """
        pass



    def getUnitsInTile(self, tileLocation):
        '''
        Returns a list of unit IDs that are located in the specified tile position
        :param tileLocation: Location object.
        :return: List of IDs
        '''

        tilePos = tileLocation.getLayerCoordinates()
        unitIDs = []
        for id in self.instance_to_agent.keys():
            unitLocation = self.instance_to_agent[id].agent.getLocation().getLayerCoordinates()
            if tilePos == unitLocation:
                unitIDs.append(id)

        print "Found ", unitIDs.__len__(), " units on this tile."
        return unitIDs

    def pump(self):
        pass


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
        self.currentTurn = not self.currentTurn
        self._world.selectUnit(None)
        self.resetAPs()
        self._world.setMode(_MODE_DEFAULT)
        ## TO-DO: add a message stating who's turn it is.
        # print self.instance_to_agent
        # for key in self.instance_to_agent.keys():
        #     instance = self.instance_to_agent[key]
        #     instance.runTurn()


    def getInstance(self, id):
        '''
        ##!!!! See if we can get rid of this by replacing it with instance_to_agent .agent
        :param id: FIFEID of the agent you want to obtain
        :return: Instance
        '''
        ids = self.agentLayer.getInstances()
        instance = [i for i in ids if i.getFifeId() == id]
        if instance:
            return instance[0]



    def applyDamage(self, location, damage):
        '''
        Deals damage to a specific location (and all the units within).
        :param location: Place where the damage is applied in the map.
        :param damage: Ammount of damage dealt
        :return:
        '''
        targetIDs = self.getUnitsInTile(location)
        for unitID in targetIDs:
            self.instance_to_agent[unitID].getDamage(damage)
            print "Unit ", unitID, "recieved damage!"

    def unitDied(self, unitID):
        '''
        Process the destruction of a unit
        :param unitID: ID of the destroyed unit
        :return:
        '''

        if unitID in self.instance_to_agent.keys():
            obj = self.instance_to_agent[unitID]
            self.instance_to_agent.__delitem__(unitID)
            self.agentLayer.deleteInstance(obj.agent)
        for player in range(2):
            if unitID in self.factionUnits[player]:
                self.factionUnits[player].remove(unitID)
        else:
            print "Could not delete instance: " , unitID


    def reset(self):
        ### TODO This should be fixed!!!
        self.instance_to_agent = {}


    def initScene(self, mapobj):
        """
		Initializess the scene and scene graph.  This creates game objects for
		FIFE instances that exist in the map.

		"""

        #initialize our scene array to some arbitrary size

        self.map, self.agentLayer = None, None
        self.cameras = {}
        self.cur_cam2_x, self.initial_cam2_x, self.cam2_scrolling_right = 0, 0, True
        self.target_rotation = 0
        self.instance_to_agent = {}
        # self.startCamera()

    # def musicHasFinished(self):
    #     """
		# Sound callback example that gets fired after the music has finished playing.
		# """
    #     print
    #     self._music.name + " has finished playing.  Starting it again...\n"


    # def endScene(self):
    #     # self._soundmanager.stopClip(self._music)
    #     self._world.endLevel()



    def load(self, filename):
        """
        Load a xml map and setup agents and cameras.
        """
        self.filename = filename
        self.reset()
        loader = fife.MapLoader(self.engine.getModel(),
                                self.engine.getVFS(),
                                self.engine.getImageManager(),
                                self.engine.getRenderBackend())

        if loader.isLoadable(filename):
            self.map = loader.load(filename)

        self._world.initCameras()
        self.initAgents()
        # self.initCameras()

        #Set background color
        self.engine.getRenderBackend().setBackgroundColor(80,80,255)



    def initAgents(self):
        """
        Setup agents.

        For this techdemo we have a very simple 'active things on the map' model,
        which is called agents. All rio maps will have a separate layer for them.

        Note that we keep a mapping from map instances (C++ model of stuff on the map)
        to the python agents for later reference.
        """
        self.agentLayer = self.map.getLayer('TechdemoMapGroundObjectLayer')

        self.hero = HumanSquad(self._world)
        self.hero.selectInstance("PC")
        self.instance_to_agent[self.hero.agent.getFifeId()] = self.hero
        self.hero.start()

        self.girl = HumanSquad(self._world)
        self.girl.selectInstance('NPC:girl')
        self.instance_to_agent[self.girl.agent.getFifeId()] = self.girl
        self.girl.start()

        # Add them to factions
        self.factionUnits[self._player1] = [self.hero.agent.getFifeId()]
        self.factionUnits[self._player2] = [self.girl.agent.getFifeId()]


        ## Spawn additional units:



        # Fog of War stuff
        #self.hero.agent.setVisitor(True)
        #self.hero.agent.setVisitorRadius(2)
        #self.girl.agent.setVisitor(True)
        #self.girl.agent.setVisitorRadius(1)

        # self.beekeepers = create_anonymous_agents(TDS, self.model, 'beekeeper', self.agentLayer, self , Beekeeper)
        # for beekeeper in self.beekeepers:
        #     self.instance_to_agent[beekeeper.agent.getFifeId()] = beekeeper
        #     self.factionUnits[self._player2].append(beekeeper.agent.getFifeId())
        #     beekeeper.start()

        # # Clouds are currently defunct.
        # cloudlayer = self.map.getLayer('TechdemoMapTileLayer')
        # self.clouds = create_anonymous_agents(TDS, self.model, 'Cloud', cloudlayer, Cloud, self)
        # for cloud in self.clouds:
        #     cloud.start(0.1, 0.05)

    def save(self, filename):
        saveMapFile(filename, self.engine, self.map)


