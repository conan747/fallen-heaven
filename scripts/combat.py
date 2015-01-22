__author__ = 'cos'



from agents.unit import *


_HEAVY, _LIGHT = xrange(2)

class Trajectory(object):
    '''
    Helps calculate if a unit can shoot to a position
    '''

    def __init__(self, unit, camera, world, weapon = 0):
        '''

        :param unit: Unit that will shoot
        :param weapon: Heavy or Light _HEAVY OR _LIGHT
        :return:
        '''

        self._unit = unit
        self._weaponMode = weapon
        self._world = world
        self._unitLocation = unit.agent.getLocation()
        self._weaponRange = 5 # to be changed!
        # self._renderer = self.cameras['main'].getRenderer('CellSelectionRenderer')
        # self._renderer.setColor(100,0,0)
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

        ## Let's try calculating a route on a fifferent layers: instead of the agentlayer, the maplayer.
        map = location.getMap()
        groundLayer = map.getLayer("GroundLayer")
        location.setLayer(groundLayer)

        # iPather = fife.RoutePather()
        unitLocation = self._unitLocation
        unitLocation.setLayer(groundLayer)
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

        loc = location
        map = location.getMap()
        groundLayer = map.getLayer("GroundLayer")
        loc.setLayer(groundLayer)

        fromLocation = self._unit.agent.getLocation()
        fromLocation.setLayer(groundLayer)

        iPather = fife.RoutePather()
        route = iPather.createRoute(fromLocation,loc, True)
        locationList = route.getPath()
        self._renderer.setEnabled(True)

        unitLayer = self._unit.agent.getLocation().getLayer()
        blocked = False
        # print "Unit layer:", unitLayer.getId()
        ## Don't use the last locations (i.e. the target) to check if it is reachable.
        if locationList.__len__() >= 2:
            locationList.pop()

        while locationList.__len__()>0:
            location = locationList.pop()
            if not location:
                continue
            location.setLayer(unitLayer)

            unitFound = unitLayer.getInstancesAt(location)
            for instance in unitFound:
                # print "Found instance: " , instance.getFifeId()
                if instance.getId() != self._unit.agent.getId():
                    blocked = True
                    # renderColor = self._renderer.getColor()
                    # self._renderer.setColor(255,0,0)
                    self._renderer.selectLocation(location)

            # self._renderer.selectLocation(location)
            # self._renderer.setColor(0,0,255)

        return not blocked