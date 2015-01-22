__author__ = 'cos'



from fife import fife
from agents.cloud import Cloud
from agents.unit import *
from agents.building import *
from fife.extensions.fife_settings import Setting

from gui.huds import TacticalHUD
from combat import Trajectory

from fife.extensions.savers import saveMapFile



_MODE_DEFAULT, _MODE_ATTACK, _MODE_DROPSHIP = xrange(3)


class Scene(object):
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

        self._music = None
        self.instance_to_agent = {}
        self.factionUnits = {}
        self._player1 = True
        self._player2 = False


    def destroyScene(self):
        """
        Removes all objects from the scene and deletes them from the layer.
        """
        pass

    def getInstacesInTile(self, tileLocation):
        '''
        Returns a list of instance IDs that are located in the specific tile.
        :param tileLocation: Exact Location of a tile.
        :return: List of instance IDs.
        '''

        tilePos = tileLocation.getLayerCoordinates()
        unitIDs = []
        all_instances = self.agentLayer.getInstances()
        for instance in all_instances:
            instanceLocation = instance.getLocation().getLayerCoordinates()
            if tilePos == instanceLocation:
                unitIDs.append(instance.getFifeId())

        print "Found ", unitIDs.__len__(), " units on this tile."
        print unitIDs
        return unitIDs


    def getInstance(self, id):
        # TODO See if we can get rid of this by replacing it with instance_to_agent .agent
        '''
        :param id: FIFEID of the agent you want to obtain
        :return: Instance
        '''
        ids = self.agentLayer.getInstances()
        instance = [i for i in ids if i.getFifeId() == id]
        if instance:
            return instance[0]

    def pump(self):
        pass

    def reset(self):
        pass

    def initScene(self, mapobj):
        """
		Initializess the scene and scene graph.  This creates game objects for
		FIFE instances that exist in the map.

		"""
        self.map, self.agentLayer = None, None
        self.cameras = {}
        self.cur_cam2_x, self.initial_cam2_x, self.cam2_scrolling_right = 0, 0, True
        self.target_rotation = 0
        self.instance_to_agent = {}


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

        id_to_class = {"PC": HumanSquad,
                    "NPC" : HumanSquad,
                    "beach_bar": Barracks}

        allInstances = self.agentLayer.getInstances()

        for instance in allInstances:
            id = instance.getId()
            unitType = id.split(":")[0]

            if unitType in id_to_class.keys():
                newUnit = id_to_class[unitType](self._world)
                newUnit.selectInstance(id)
                self.instance_to_agent[newUnit.agent.getFifeId()] = newUnit
                newUnit.start()
                print id , "loaded!"

                if isinstance(newUnit,Building):
                    newUnit.setFootprint()

                ## FIXME: A fix to test the loading of units
                if id == "PC":
                    self.factionUnits[self._player1] = [newUnit.agent.getFifeId()]
                elif id == "NPC":
                    self.factionUnits[self._player2] = [newUnit.agent.getFifeId()]



    def save(self, filename):
        print "Saving map..."
        saveMapFile(filename, self.engine, self.map)
