__author__ = 'cos'


from fife import fife

import cPickle as pickle

class Action(object):
    '''
    This is an abstract class that will subsample into more especific actions.
    Each action can serialize itself. Also unserialize via constructor.

    actionMessage should be a list containing the fields:
    [actionID, *args]

    actionID will take care of properly parsing *args.
    '''
    _MOVE, _ATTACK, _GETIN, _GETOUT = xrange(4)
    @classmethod
    def getAction(cls, message):
        '''
        Creates a proper action from a serialized message.
        :param message: List containing the serialized action message.
        :return: Corresponding instance of the proper class Action.
        '''
        actionType = message[0]
        args = message[1:]
        if actionType == cls._MOVE:
            return AMove(*args)
        elif actionType == cls._ATTACK:
            return AAttack(*args)
        elif actionType == cls._GETIN:
            return AGetIn(*args)
        elif actionType == cls._GETOUT:
            return  AGetOut(*args)

        else:
            print "Error: Wrong action type %d" % actionType
            return None


    def serialize(self):
        pass

    def execute(self, combatPlayer):
        '''
        It should be able to call the proper method on combatPlayer to be able to execute itself.
        :param combatPlayer: The current combat player object
        :return:
        '''
        pass

class AMove(Action):
    '''
    Describes the movement of an agent.
    '''

    def __init__(self, agent, destination):
        self.agentID = agent
        self.destination = destination

    def serialize(self):
        return [self._MOVE, self.agentID, self.destination]

    def execute(self, combatPlayer):
        combatPlayer.move(self)

class AAttack(Action):
    '''
    Handles a perfect attack.
    '''
    def __init__(self, agent, destination, weaponType):
        self.agentID = agent
        self.destination = destination
        self.weaponType = weaponType

    def serialize(self):
        return [self._ATTACK, self.agentID, self.destination, self.weaponType]

    def execute(self, combatPlayer):
        combatPlayer.attack(self)

class AGetIn(Action):
    '''
    Moves an agent into a storage.
    '''
    def __init__(self, agent, storageOwner, iconName):
        self.agentID = agent
        self.storageOwnerID = storageOwner
        self.iconName = iconName

    def serialize(self):
        return [self._GETIN, self.agentID, self.storageOwnerID, self.iconName]

    def execute(self, combatPlayer):
        combatPlayer.getIn(self)

class AGetOut(Action):
    '''
    Brings an agent out of the storage.
    '''
    def __init__(self, agent, storageOwner, destination, inStorageID):
        self.agentID = agent
        self.storageOwnerID = storageOwner
        self.destination = destination
        self.inStorageID = inStorageID

    def serialize(self):
        return [self._GETOUT, self.agentID, self.storageOwnerID, self.destination, self.inStorageID]

    def execute(self, combatPlayer):
        combatPlayer.getOut(self)



class CombatRecorder(object):
    '''
    This class records combat actions, logs them, serializes them and finally also sends them so that a CombatPlayer can read them.
    '''

    def __init__(self, universe):
        self.universe = universe
        self.turnActions = [] #Holds a list of all the actions for this turn.
        self.recording = True

    def serializeLocation(self, location):
        point3d = location.getLayerCoordinates()
        return (point3d.x, point3d.y, point3d.z)

    def onMoved(self, agent, location):
        '''
        The method records a moving agent.
        :param agent: Agent (normally unit) that has moved.
        :param location: place where the agent moved
        :return:
        '''
        if not self.recording:
            return
        agentName = agent.agentName
        destination = self.serializeLocation(location)
        action = AMove(agentName, destination)
        self.turnActions.append(action)

    def onAttack(self, agent, location, weaponType):
        '''
        This method should be called to record an attack.
        :param agent: Agent that performs the attack.
        :param location: Place where the projectile struck (not where it was originally aimed!)
        :param weaponType: light or heavy weapon that was fired.
        :return:
        '''
        if not self.recording:
            return
        agentName = agent.agentName
        destination = self.serializeLocation(location)
        action = AAttack(agentName, destination, weaponType)
        self.turnActions.append(action)

    def onGetIn(self, agent, storage, iconName):
        '''
        :param agent:
        :param storageOwner:
        :return:
        '''
        if not self.recording:
            return

        agentName = agent.agentName
        storageOwner = storage.parent.agentName
        action = AGetIn(agentName, storageOwner, iconName)
        self.turnActions.append(action)

    def onGetOut(self, agent, storage, location, inStorageID):
        '''

        :param agent:
        :param storage:
        :return:
        '''
        if not self.recording:
            return

        agentName = agent.agentName
        storageOwner = storage.parent.agentName
        destination = self.serializeLocation(location)
        action = AGetOut(agentName, storageOwner, destination, inStorageID)
        self.turnActions.append(action)


    def dumpTurn(self):
        '''
        Returns the list containing recorded turn messages.
        :return:
        '''
        return [action.serialize() for action in self.turnActions]

    def saveFile(self):
        '''
        Pickles a file with the actions.
        :return:
        '''
        list = self.dumpTurn()
        pickle.dump(list, open("saves/test.action" , 'wb'))



class CombatPlayer(object):
    '''
    This class is able to read the turnActions message and reproduce the turn.
    '''

    def __init__(self, universe, turnMessages=None):

        self.universe = universe
        self.unitManager = universe.world.unitManager

        self.turnMessages = None
        self.reproducing = False

        if turnMessages:
            self.turnMessages = turnMessages

    def carryOn(self):
        if not self.reproducing:
            return
        if not self.turnMessages:
            self.reproducing = False
            self.universe.world.combatRecorder.recording = True
        else:
            self.reproduce()

    def reproduce(self, turnMessages=None):

        if turnMessages:
            self.turnMessages = turnMessages

        if not self.turnMessages:
            print "Error: No turn turnMessages indicated."
            return

        self.reproducing = True
        self.universe.world.combatRecorder.recording = False

        if self.turnMessages:
            message = self.turnMessages.pop(0)
            action = Action.getAction(message)
            if not action:
                self.carryOn()
                return

            action.execute(self)

    def getAgent(self, agentName):
        '''
        Return the agent that has the corresponding agentName.
        :param agentName: name of the agent
        :return: Agent itself
        '''
        return self.unitManager.getAgent(agentName)

    def move(self, action):

        agent = self.getAgent(action.agentID)
        if not agent:
            print "Error: %s not found!" % action.agentID
        location = agent.instance.getLocation()
        point = fife.Point3D(*action.destination)
        location.setLayerCoordinates(point)
        agent.run(location)

    def attack(self, action):

        agent = self.getAgent(action.agentID)
        location = agent.instance.getLocation()
        point = fife.Point3D(*action.destination)
        location.setLayerCoordinates(point)

        agent.shoot(location, action.weaponType)


    def getIn(self, action):
        agent = self.getAgent(action.agentID)
        storageOwner = self.getAgent(action.storageOwnerID)
        storage = storageOwner.storage
        iconName = action.iconName

        if storage.addUnit(agent, iconName):
            ## storage added correctly -> remove unit from the map.
            agent.die()

        self.carryOn()

    def getOut(self, action):

        storageOwner = self.getAgent(action.storageOwnerID)

        storage = storageOwner.storage
        inStorageID = action.inStorageID

        location = storageOwner.instance.getLocation()
        point = fife.Point3D(*action.destination)
        location.setLayerCoordinates(point)

        unitName = inStorageID.split(":")[1]
        unit = self.universe.world.unitLoader.createUnit(unitName)
        unit.agentName = action.agentID
        unit.createInstance(location)
        unit.instance.setId(unit.agentName)

        # Generate an instance for the unit.
        instanceID = unit.instance.getFifeId()
        faction = unit.properties["faction"]
        self.universe.world.factionUnits[faction].append(instanceID)
        self.universe.world.view.addPathVisual(unit.instance)
        storage.unitDeployed(inStorageID)

        self.carryOn()

    def loadActions(self):
        list = pickle.load(open("saves/test.action" , 'r'))
        self.reproduce(list)
