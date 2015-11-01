__author__ = 'cos'



from fife import fife
from agents.cloud import Cloud
# from agents.unit import *
# from agents.building import *
from fife.extensions.fife_settings import Setting

from gui.huds import TacticalHUD
from combat import Trajectory

from fife.extensions.savers import saveMapFile
import cPickle as pickle


# Temp:
import os


_MODE_DEFAULT, _MODE_ATTACK, _MODE_DROPSHIP = xrange(3)



class Scene(object):
    """
    Master game scene.  Keeps track of all game objects.

    This is the meat and potatoes of the game.  This class takes care of all the units.
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
        self.faction = self._world.faction
        self.planet = self._world.planet

        self.unitLoader = self._world.universe.unitLoader

    def destroy(self):
        """
        Removes all objects from the scene and deletes them from the layer.
        """
        for agent in self.instance_to_agent.values():
            if hasattr(agent, "storage"):
                del agent.storage
            del agent

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


    def load(self, filename):
        """
        Load a xml map and setup agents and cameras.
        """
        self.filename = filename
        loader = fife.MapLoader(self.engine.getModel(),
                                self.engine.getVFS(),
                                self.engine.getImageManager(),
                                self.engine.getRenderBackend())

        if not loader.isLoadable(filename):
            print "Problem loading map: map file is not loadable"
            return

        self.map = loader.load(filename)

        self._world.initCameras()
        self.initAgents()
        # self.initCameras()

        #Set background color
        self.engine.getRenderBackend().setBackgroundColor(0,0,0)


        ## Load storages:
        '''
        storageFile = filename.replace(".xml",".sto")
        if os.path.isfile(storageFile):
            pic = pickle.load(open(storageFile, 'rb'))
            for building in self.instance_to_agent.values():
                if building.agentName in pic.keys():
                    info = pic[building.agentName]
                    print "Setting up", info
                    building.storage.setStorage(info)
        '''


    def initAgents(self):
        """
        Setup agents.

        Loads the "agents" (i.e. units and structures) from the planet object and initialises them.
        """

        self.agentLayer = self.map.getLayer('TechdemoMapGroundObjectLayer')
        if not self.agentLayer:
            print "Using the first layer that was found: ", self.map.getLayers()[0].getId()
            self.agentLayer = self.map.getLayers()[0]

        agentList = self.planet.agentInfo
        self.planet.agentInfo = {}

        for agentID in agentList.keys():
            id = agentID
            agentType = id.split(":")[0] # Holds the unit or stucture name

            if self.unitLoader.isUnit(agentType):
                newUnit = self.unitLoader.createUnit(agentType)
                newUnit.AP = agentList[agentID]["AP"]
            elif self.unitLoader.isBuilding(agentType):
                newUnit = self.unitLoader.createBuilding(agentType)
            else:
                print "Error: unit is not building nor unit! ??"
                continue

            location = agentList[agentID]["Location"]
            newUnit.createInstance(location)
            self.instance_to_agent[newUnit.agent.getFifeId()] = newUnit
            newUnit.start()

            # Apply storage:
            if agentID in self.planet.storages.keys():
                storage = self.planet.storages[agentID]
                if storage:
                    newUnit.storage.setStorage(storage)
                    self.planet.storages[agentID] = None



            # Apply health:
            newUnit.health = agentList[agentID]["HP"]

            print id , "loaded!"

                    # if newUnit.nameSpace == "Building":
                    #     newUnit.setFootprint()

    def updatePlanetAgents(self):
        '''
        Updates the agent information (units and structures) that the planet object stores.
        :return:
        '''
        self.planet.agentInfo = {}
        for angent in self.instance_to_agent.values():
            self.planet.saveInstance(angent)



    def getStorageDicts(self):
        '''
        Return a dictionary containing the storages of the buildings in this scene.
        :return:
        '''
        storages = {}

        for agentName in self.instance_to_agent.keys():
            agent = self.instance_to_agent[agentName]
            if agent.agentType == "Building":
                if agent.storage:
                    # Add this to the storages
                    if agent.storage.inProduction or agent.storage.unitsReady:
                        thisStorage = agent.storage.getStorageDict()
                        storages[agent.agentName] = thisStorage

        print "Saving" , len(storages), "storages"

        return storages


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

            self.agentLayer.deleteInstance(unit.agent)
            unit.agent = None

        else:
            print "Could not delete instance: " , unitID