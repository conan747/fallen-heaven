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
from agents.agent import Agent


# Temp:
import os


_MODE_DEFAULT, _MODE_ATTACK, _MODE_DROPSHIP = xrange(3)



class UnitManager(object):
    '''
    This object will hold a reference to all the Agents on map and help access them.
    '''

    def __init__(self):

        self.fife2Agent = {} # What before was instance to agent.
        self.ID2fife = {}  # Maps IDs with their corresponding fifeID.
        #self.world = world
        #self.unitLoader = self._world.universe.unitLoader

        self.getAgents = self.fife2Agent.values
        self.getFifeIds = self.fife2Agent.keys

        self.getIDs = self.ID2fife.keys

        self.dummyIDs = {}


    def destroy(self):
        """
        Removes all objects from the scene and deletes them from the layer.
        """
        #TODO: Re-check this method
        for id in self.fife2Agent.keys():
            self.unitDied(id)

        for agent in self.fife2Agent.values():
            if hasattr(agent, "storage"):
                del agent.storage
            del agent

    def fife2Agent(self, id):
        '''
        Returns the agent that has a certain FifeId.  Substitutes instance_to_agent
        :param id: FifeID of the instance
        :return: Agent.
        '''
        return self.fife2Agent[id]

    def addAgent(self, newAgent, location):
            newAgent.createInstance(location)
            fifeID = newAgent.instance.getFifeId()
            self.fife2Agent[fifeID] = newAgent
            self.ID2fife[newAgent.instance.getId()] = fifeID

            newAgent.start()
            if hasattr(newAgent, "dummyInstances"):
                dummyList = [dummy.getFifeId() for dummy in  newAgent.dummyInstances]
                self.dummyIDs[fifeID] = dummyList

    def getFifeId(self, argument):
        '''
        Returns the fife id of the relevant instance.
        :param argument: Instance, fifeID or Agent
        :return: fifeID (long)
        '''
        if isinstance(argument, Agent):
            argument = argument.instance.getFifeId()
        if argument:
            return self.getAgent(argument).instance.getFifeId()

    def getAgent(self, argument):
        '''
        Returns the agent corresponding to Instance or fifeID
        :param argument: Instance or fifeID
        :return: Agent
        '''
        if isinstance(argument, fife.Instance):
            argument = argument.getFifeId()

        if argument in self.getFifeIds():
            return self.fife2Agent[argument]
        else:
            parentID = [key for key, value in self.dummyIDs.items() \
                      if argument in value]
            if parentID:
                return self.fife2Agent[parentID[0]]

    def initAgents(self, map, agentList, unitLoader, planet):
        """
        Setup agents.

        Loads the "agents" (i.e. units and structures) from the planet object and initialises them.
        """
        #self.map # Can I get away with not defining this?
        self.agentLayer = map.getLayer('TechdemoMapGroundObjectLayer')
        if not self.agentLayer:
            print "Using the first layer that was found: ", map.getLayers()[0].getId()
            self.agentLayer = map.getLayers()[0]

        for agentID in agentList.keys():
            agentType = agentID.split(":")[0] # Holds the unit or stucture name

            if unitLoader.isUnit(agentType):
                newAgent = unitLoader.createUnit(agentType)
                newAgent.AP = agentList[agentID]["AP"]
            elif unitLoader.isBuilding(agentType):
                newAgent = unitLoader.createBuilding(agentType)
            else:
                print "Error: unit is not building nor unit! ??"
                continue

            location = agentList[agentID]["Location"]
            self.addAgent(newAgent, location)

            # Apply storage:
            if agentID in planet.storages.keys():
                storage = planet.storages[agentID]
                if storage:
                    newAgent.storage.setStorage(storage)
                    planet.storages[agentID] = None

            # Apply health:
            newAgent.health = agentList[agentID]["HP"]

            print agentID , "loaded!"

    def addBuilding(self, building):
        building.start()
        self.fife2Agent[building.instance.getFifeId()] = building

    def saveAllAgents(self, planet):
        '''
        Saves all the intances.
        :param planet: The planet object.
        :return:
        '''
        for angent in self.getAgents():
            planet.saveInstance(angent)

    def getStorageDicts(self):
        '''
        Return a dictionary containing the storages of the buildings in this scene.
        :return:
        '''
        storages = {}

        for agent in self.getAgents():
            if agent.agentType == "Building":
                if agent.storage:
                    # Add this to the storages
                    if agent.storage.inProduction or agent.storage.unitsReady:
                        thisStorage = agent.storage.getStorageDict()
                        storages[agent.agentName] = thisStorage
        return storages

    def removeInstance(self, fifeID):
        '''
        Process the destruction of a unit
        :param fifeID: FifeID or instace or agent of the destroyed unit
        :return:
        '''
        if isinstance(fifeID, Agent):
            agent = fifeID
            fifeID = fifeID.instance.getFifeId()
        else:
            agent = self.getAgent(fifeID)
            if isinstance(fifeID, fife.Instance):
                fifeID = fifeID.instance.getFifeId()

        if agent:
            self.fife2Agent.__delitem__(fifeID)
            agent.instance.removeActionListener(agent)

            self.agentLayer.deleteInstance(agent.agent)
            agent.instance = None

            if fifeID in self.dummyIDs.keys():
                self.fife2Agent.__delitem__(fifeID)

        else:
            print "Could not delete instance: " , fifeID


    def teleport(self, id, location):
        '''
        Teleports given unit to a certain location
        :param id: FifeID of the unit.
        :param location: location to teleport to.
        :return:
        '''
        self.getAgent(id).teleport(location)


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
        self.factionUnits = {}
        self._player1 = True
        self._player2 = False
        self.faction = self._world.faction
        self.planet = self._world.planet

        self.unitLoader = self._world.universe.unitLoader
        self.unitManager = None

    def destroy(self):
        """
        Removes all objects from the scene and deletes them from the layer.
        """
        self.unitManager.destroy()


    def getInstance(self, id):
        '''
        :param id: FIFEID of the agent you want to obtain
        :return: Instance
        '''
        return self.unitManager.getAgent(id)

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

        self.map.initializeCellCaches()
        self.map.finalizeCellCaches()

        self.agentLayer = self.map.getLayer('TechdemoMapGroundObjectLayer')

        self.unitManager = UnitManager()

        self._world.initCameras()
        self.initAgents()
        # self.initCameras()

        #Set background color
        self.engine.getRenderBackend().setBackgroundColor(0,0,0)


        ## Load storages:
        # '''
        # storageFile = filename.replace(".xml",".sto")
        # if os.path.isfile(storageFile):
        #     pic = pickle.load(open(storageFile, 'rb'))
        #     for building in self.instance_to_agent.values():
        #         if building.agentName in pic.keys():
        #             info = pic[building.agentName]
        #             print "Setting up", info
        #             building.storage.setStorage(info)
        # '''


    def initAgents(self):
        """
        Setup agents.

        Loads the "agents" (i.e. units and structures) from the planet object and initialises them.
        """

        agentList = self.planet.agentInfo
        self.unitManager.initAgents(self.map, agentList, self._world.universe.unitLoader, self.planet)
        self.planet.agentInfo = {}
        

    def updatePlanetAgents(self):
        '''
        Updates the agent information (units and structures) that the planet object stores.
        :return:
        '''
        self.planet.agentInfo = {}
        self.unitManager.saveAllAgents(self.planet)


    def getStorageDicts(self):
        '''
        Return a dictionary containing the storages of the buildings in this scene.
        :return:
        '''
        return self.unitManager.getStorageDicts()
        storages = {}


    def unitDied(self, fifeID):
        '''
        Process the destruction of a unit
        :param fifeID: ID of the destroyed unit
        :return:
        '''
        self.unitManager.removeInstance(fifeID)