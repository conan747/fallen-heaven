# -*- coding: utf-8 -*-

# ####################################################################
#  Copyright (C) 2005-2013 by the FIFE team
#  http://www.fifengine.net
#  This file is part of FIFE.
#
#  FIFE is free software; you can redistribute it and/or
#  modify it under the terms of the GNU Lesser General Public
#  License as published by the Free Software Foundation; either
#  version 2.1 of the License, or (at your option) any later version.
#
#  This library is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#  Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public
#  License along with this library; if not, write to the
#  Free Software Foundation, Inc.,
#  51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
# ####################################################################

from fife import fife
from agent import Agent
from fife.extensions.fife_settings import Setting




_STATE_NONE, _STATE_IDLE, _STATE_RUN, _STATE_KICK, _STATE_TALK = xrange(5)

_LWEAPON, _HWEAPON = xrange(2)
_INFANTRY, _GROUND, _HOOVER = xrange(3)

## TODO: Perhaps I could encapsulate common methods with the Unit class? This should be added to the Agent class I guess.

class Building(Agent):

    agent = None

    movement = None
    lightWeapon = None
    heavyWeapon = None
    properties = None
    landed = False


    def __init__(self, unitName, world):
        self.nameSpace = "Building"
        super(Building, self).__init__(unitName, self.nameSpace, world)
        # self.agent = layer.getInstance(agentName)
        self._renderer = None
        self._SelectRenderer = None
        self.cellCache = None


    # def onInstanceActionFinished(self, instance, action):
    #     pass


    def onInstanceActionCancelled(self, instance, action):
        pass


    def start(self):
        pass


    def idle(self):
        self.state = _STATE_IDLE
        self.agent.actOnce('stand')


    def calculateDistance(self,location):
        # print "Current Location", self.agent.getLocation().getMapCoordinates()
        # print "Target Location", location.getMapCoordinates()
        iPather = fife.RoutePather()
        route = iPather.createRoute(self.agent.getLocation(),location, True)
        # print "Beginning of the route", route.getStartNode().getMapCoordinates()
        # print "End of the route", route.getEndNode().getMapCoordinates()
        # if iPather.solveRoute(route):
            # print "Route solved!"
        # route = fife.Route(self.agent.getLocation(),location)
        # path = route.getPath()
        distance = route.getPathLength()
        # print "Distance to walk:", distance
        # pathList = route.getPath()
        # print "Path coordinates:"
        # for location in pathList:
        #     print location.getMapCoordinates()
        # print "End path coords"
        return distance


    def resetAP(self):
        self.properties.AP = self.properties._maxAP

    def teleport(self, location):
        if self.landed:
            print "Can't teleport! Already constructed here!"
            return False

        exactcoords = location.getLayerCoordinates()
        layercoords = fife.DoublePoint3D(int(exactcoords.x), int(exactcoords.y), int(exactcoords.z) )
        location.setExactLayerCoordinates(layercoords)

        if location == self.agent.getLocation():
            return True

        # unblocked = True
        for x in range( self.properties._sizeX):
            for y in range( self.properties._sizeY):
                # if (x or y) == 0:
                #     continue
                # loc = self.agent.getLocation()
                cellPos = location.getLayerCoordinates()
                cellPos.x += x
                cellPos.y -= y

                layer = self.agent.getLocation().getLayer()
                if not self.cellCache:
                    self.cellCache = layer.getCellCache()
                cell = self.cellCache.getCell(cellPos)
                if cell.getCellType() != fife.CTYPE_NO_BLOCKER:
                    return False

        # ## Check if the location is empty:
        # if not self.world.scene.getInstacesInTile(location):
        self.agent.setLocation(location)
        return True


    def die(self):
        print "This unit is destroyed!"
        self.world.scene.unitDied(self.agent.getFifeId())
        # self.layer.deleteInstance(self.agent)


    def attack(self, location, weaponType=_LWEAPON):
        if weaponType == _LWEAPON:
            self.lightWeapon.fire(location)
        elif weaponType == _HWEAPON:
            self.heavyWeapon.fire(location)


    def getDamage(self, dmg):
        print "Previous health: " , self.properties.health
        print "Dealing ", dmg, " damage!"
        self.properties.health -= dmg
        if self.properties.health <= 0:
            self.die()

    def onInstanceActionFinished(self, instance, action):
        pass


    def createInstance(self, location):
        super(Building,self).createInstance(location)
        print "Instance Created!"


    def setFootprint(self):
        '''
        Sets the cells under this instance as blocking.
        :return:
        '''
        for x in range( self.properties["SizeX"]):
            for y in range( self.properties["SizeY"]):
                location = self.agent.getLocation()
                cellPos = location.getLayerCoordinates()
                cellPos.x += x
                cellPos.y -= y

                layer = location.getLayer()
                cellCache = layer.getCellCache()
                cell = cellCache.getCell(cellPos)
                cell.setCellType(fife.CTYPE_STATIC_BLOCKER)

        self.landed = True