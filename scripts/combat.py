__author__ = 'cos'



from agents.unit import *


#_LIGHT, _HEAVY = xrange(2)

class Retaliation(object):
    '''
    Handles keeping track of the units that have retaliated against a given unit.
    '''

    def __init__(self, world, targetAgent):
        self.world = world
        self.targetAgent = targetAgent
        self.targetId = targetAgent.instance.getFifeId()
        self.targetLocation = targetAgent.instance.getLocation()

        enemyName = [name for name in self.world.factionUnits.keys()
                     if name is not self.world.currentTurn][0]

        self.enemyUnits = self.world.factionUnits[enemyName]
        self.retaliatedUnits = []
        self.availableUnits = {}
        self.world.busy = True
        self.unitManager = self.world.unitManager

        self.getAvailable()

    def getAvailable(self):
        '''
        Gets the units that are able to retaliate.
        '''
        for id in self.enemyUnits:
            agent = self.unitManager.getAgent(id)
            if not hasattr(agent, "canAttack"):
                continue
            if agent.canAttack(agent.HWEAPON):
                weaponType = agent.HWEAPON
            elif agent.canAttack(agent.LWEAPON):
                weaponType = agent.LWEAPON
            else:
                continue

            # If we got here it's because we have a unit that can attack.
            # See if the agent is in range.
            trajectory = Trajectory(agent, self.world, weaponType)
            if trajectory.hasClearPath(self.targetLocation):
                self.availableUnits[id] = weaponType

        if not self.availableUnits:
            self.cleanup()

    def next(self):
        '''
        Handles the next available retaliation.
        '''
        print "retaliating next"
        if not self.unitManager.getAgent(self.targetId):
            # Target has died. Stop retaliation.
            self.cleanup()
            return

        if not self.availableUnits:
            # There are no other units that can retaliate.
            self.cleanup()
            return

        (id, weaponType ) = self.availableUnits.popitem()
        attackingUnit = self.unitManager.getAgent(id)
        if attackingUnit:
            print "unit that is retaliating: ", attackingUnit.agentName
            attackingUnit.attack(self.targetLocation, weaponType)

        if not self.availableUnits:
            self.cleanup()
            return


    def cleanup(self):
        self.world.busy = False
        self.world.retaliation = None





class Trajectory(object):
    '''
    Helps calculate if a unit can shoot to a position
    '''

    def __init__(self, unit, world, weapon = 0):
        '''
        :param unit: Unit that will shoot
        :param weapon: Heavy or Light unit.LWEAPON OR unit.HWEAPON
        :return:
        '''

        self._unit = unit
        self._weaponMode = weapon
        self._world = world
        self._unitLocation = unit.instance.getLocation()
        if self._weaponMode == self._unit.LWEAPON:
            self.weapon = self._unit.lightWeapon
        elif self._weaponMode ==  self._unit.HWEAPON:
            self.weapon = self._unit.heavyWeapon

        self._weaponRange = self.weapon.properties["Range"]
        # self._renderer = self.cameras['main'].getRenderer('CellSelectionRenderer')
        # self._renderer.setColor(100,0,0)
        camera = world.cameras['main']
        self._renderer = fife.CellSelectionRenderer.getInstance(camera)
        self._genericrenderer = fife.GenericRenderer.getInstance(camera)
        self._genericrenderer.activateAllLayers(self._world.map)
        self.unitManager = self._world.unitManager

    def canShoot(self, location, display=False):
        '''
        Tells if a unit can shoot to a specific location.
        :param location: Target location
        :return: bool.
        '''
        if not self.isInRange(location):
            return False

        if not self.weapon.properties["Parabolic"]:
            if not self.hasClearPath(location, display):
                return False

        return True


    def isInRange(self, location):
        '''
        Tells if the location is in range with the weapon.
        :param location: Target Location
        :return: bool
        '''

        ## Let's try calculating a route on a fifferent layer: instead of the agentlayer, the maplayer.
        map = location.getMap()
        trajectoryLayer = map.getLayer("TrajectoryLayer")
        location.setLayer(trajectoryLayer)

        # iPather = fife.RoutePather()
        unitLocation = self._unitLocation
        unitLocation.setLayer(trajectoryLayer)
        distance = unitLocation.getLayerDistanceTo(location)
        if distance == 0:
            return False
        # print "Shot length" , distance
        return (distance <= self._weaponRange)
        # route = iPather.createRoute(unitLocation,location, True)
        # if not iPather.solveRoute(route, 1, True):
        #     print "Problem solving route!"
        # print "Shot length" , route.getPathLength()
        # print "From" , unitLocation.getLayerCoordinates()
        # print "To" , location.getLayerCoordinates()
        # return (route.getPathLength() <= self._weaponRange)

    def hasClearPath(self, location, display=False):
        '''
        Returns if there is anything between the unit and the target.
        :param location: target
        :return: bool
        '''

        instancerenderer = fife.InstanceRenderer.getInstance(self._world.cameras["main"])
        instancerenderer.removeAllColored()
        instancerenderer.removeAllOutlines()

        self._renderer.reset()
        fromLocation = self._unit.instance.getLocation()
        layer = fromLocation.getLayer()
        origin = fromLocation.getLayerCoordinates(layer)
        destination = location.getLayerCoordinates(layer)
        exclude = [self._unit.instance]
        target = layer.getInstancesAt(location)
        exclude += target
        exclude = [self.unitManager.getFifeId(agent) for agent in exclude]


        self._genericrenderer.removeAll("LineOfSight")

        if display:
            fromNode = fife.RendererNode(fromLocation)
            toNode = fife.RendererNode(location)
            self._genericrenderer.addLine("LineOfSight", fromNode, toNode, 255, 225, 225, 255)
            self._genericrenderer.setEnabled(True)
        # self._renderer.setEnabled(True)
        # self._renderer.setColor(0,0,255)

        instances = layer.getInstancesInLine(origin, destination)

        for instance in instances:
            agent = self.unitManager.getAgent(instance)
            if agent:
                instance = agent.instance
            if instance.getFifeId() not in exclude:
                #print "Instance found on path: ", instance.getFifeId()
                instancerenderer.addColored(instance, 250, 50, 100)
                return False

        return True