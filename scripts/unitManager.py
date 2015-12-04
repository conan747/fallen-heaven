__author__ = 'cos'



from fife import fife
from agents.agent import Agent



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

        for agent in self.fife2Agent.values():
            if hasattr(agent, "storage"):
                agent.storage = None
            self.removeInstance(agent)


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
        if not argument:
            return None

        if isinstance(argument, fife.Instance):
            argument = argument.getFifeId()

        if argument in self.getFifeIds():
            return self.fife2Agent[argument]
        elif ":" in str(argument):
            # This means that we are looking for a "agentName" instead of a fifeID
            print "Looking for %s in unit names." % argument
            for agent in self.getAgents():
                if argument== agent.agentName:
                    return agent
        else:
            parentID = [key for key, value in self.dummyIDs.items() \
                      if argument in value]
            if parentID:
                return self.fife2Agent[parentID[0]]

    def initAgents(self, layer, agentList, unitLoader, planet):
        """
        Setup agents.

        Loads the "agents" (i.e. units and structures) from the planet object and initialises them.
        """
        #self.map # Can I get away with not defining this?
        self.agentLayer = layer

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
        planet.agentInfo = {}
        for angent in self.getAgents():
            planet.saveInstance(angent)

    def getStorageDicts(self):
        '''
        Return a dictionary containing the storages of the buildings in this scene.
        :return:
        '''
        storages = {}
        ##FIXME: Should this take into account faction?

        for agent in self.getAgents():
            if agent.agentType == "Building":
                if agent.storage:
                    # Add this to the storages
                    if agent.storage.inProduction or agent.storage.unitsReady:
                        thisStorage = agent.storage.getStorageDict()
                        storages[agent.agentName] = thisStorage
        return storages

    def removeInstance(self, arg, soft=False):
        '''
        Process the destruction of a unit
        :param fifeID: FifeID or instace or agent of the destroyed unit
        :return:
        '''
        if isinstance(arg, Agent):
            agent = arg
            fifeID = arg.instance.getFifeId()
        else:
            agent = self.getAgent(arg)
            fifeID = agent.instance.getFifeId()

        if agent:
            agent.instance.removeActionListener(agent)

            if fifeID in self.dummyIDs.keys():
                agent.removeFootprint()
                self.dummyIDs.__delitem__(fifeID)

            self.fife2Agent.__delitem__(fifeID)

            if not soft:
                self.agentLayer.deleteInstance(agent.instance)
            agent.instance = None

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
