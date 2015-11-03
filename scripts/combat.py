__author__ = 'cos'



from agents.unit import *


#_LIGHT, _HEAVY = xrange(2)

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
        self._unitLocation = unit.agent.getLocation()
        if self._weaponMode == self._unit.LWEAPON:
            self.weapon = self._unit.lightWeapon
        elif self._weaponMode ==  self._unit.HWEAPON:
            self.weapon = self._unit.heavyWeapon

        self._weaponRange = self.weapon.properties["Range"]
        # self._renderer = self.cameras['main'].getRenderer('CellSelectionRenderer')
        # self._renderer.setColor(100,0,0)
        camera = world.cameras['main']
        self._renderer = fife.CellSelectionRenderer.getInstance(camera)

    def canShoot(self, location):
        '''
        Tells if a unit can shoot to a specific location.
        :param location: Target location
        :return: bool.
        '''
        if not self.isInRange(location):
            return False

        if not self.hasClearPath(location):
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

    def hasClearPath(self, location):
        '''
        Returns if there is anything between the unit and the target.
        :param location: target
        :return: bool
        '''

        self._renderer.reset()
        fromLocation = self._unit.agent.getLocation()
        layer = fromLocation.getLayer()
        origin = fromLocation.getLayerCoordinates(layer)
        destination = location.getLayerCoordinates(layer)
        exclude = [self._unit.agent]
        target = layer.getInstancesAt(location)
        exclude += target
        exclude = [agent.getFifeId() for agent in exclude]

        instances = layer.getInstancesInLine(origin, destination)
        # self._renderer.setEnabled(True)
        # self._renderer.setColor(0,0,255)

        for instance in instances:
            if instance.getFifeId() not in exclude:
                #print "Instance found on path: ", instance.getFifeId()
                return False

        return True