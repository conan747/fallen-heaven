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
from weapon import *




_STATE_NONE, _STATE_IDLE, _STATE_RUN, _STATE_KICK, _STATE_TALK = xrange(5)

_WALK, _LAND, _AIR = xrange(3)
_INFANTRY, _GROUND, _HOOVER = xrange(3)
_LWEAPON, _HWEAPON = xrange(2)


class UnitProperties(object):

    _maxHealth = None
    health = None
    _unitType = None
    _cost = None
    _maxAP = None
    AP = None
    _faction = None
    _unitName = None # common name of the unit

    # namespaceId #included in Model

    def initialize(self):
        self.health = self._maxHealth
        self.AP = self._maxAP
    # def __init__(self, maxHealth, unitType, cost):
    #     self._maxHealth = maxHealth
    #     self._unitType = unitType
    #     self._health = maxHealth
    #     self._cost = cost


class Unit(Agent):

    instance = None

    movement = None
    lightWeapon = None
    heavyWeapon = None
    properties = UnitProperties()


    def __init__(self, settings, model, agentName, layer, world, uniqInMap=True):
        super(Unit, self).__init__(settings, model, agentName, layer, world, uniqInMap)
        self.instance = layer.getInstance(agentName)

        self._renderer = None


    # def onInstanceActionFinished(self, instance, action):
    #     pass


    def onInstanceActionCancelled(self, instance, action):
        pass


    def start(self):
        self.idle()


    def idle(self):
        self.state = _STATE_IDLE
        self.agent.actOnce('stand')


    def calculateDistance(self,location):
        # print "Current Location", self.instance.getLocation().getMapCoordinates()
        # print "Target Location", location.getMapCoordinates()
        iPather = fife.RoutePather()
        route = iPather.createRoute(self.instance.getLocation(),location, True)
        # print "Beginning of the route", route.getStartNode().getMapCoordinates()
        # print "End of the route", route.getEndNode().getMapCoordinates()
        # if iPather.solveRoute(route):
            # print "Route solved!"
        # route = fife.Route(self.instance.getLocation(),location)
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


    def run(self, location):

        if not self._renderer:
            self._renderer = fife.CellSelectionRenderer.getInstance(self.world.cameras['main'])

        self._renderer.setEnabled(False)
        self.state = _STATE_RUN
        movesLeft = self.properties.AP / 10

        iPather = fife.RoutePather()
        route = iPather.createRoute(self.instance.getLocation(),location, True)
        route.cutPath(movesLeft) ## Cut the path short if too long
        self.properties.AP -= route.getPathLength() *10
        print "Path length:", route.getPathLength()

        ## Test

        self._renderer.reset()
        self._renderer.setColor(0,0,255)
        locationList = route.getPath()
        while locationList.__len__()>0:
            location = locationList.pop()
            self._renderer.selectLocation(location)

        self._renderer.setEnabled(True)


        self.agent.move('run', route.getEndNode(), 4 * self.settings.get("rio", "TestAgentSpeed"))


    def kick(self, target):
        self.state = _STATE_KICK
        self.agent.actOnce('kick', target)


    def talk(self, target):
        self.state = _STATE_TALK
        self.agent.actOnce('talk', target)


    def die(self):
        print "This unit is dead!"
        self.world.unitDied(self.agent.getFifeId())
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
        if self._renderer:
            # self._renderer.setEnabled(False) ## instead do self._renderer.reset()
            self._renderer.reset()
            self.idle()

# class Movement(object):
#     ''' Describes the type of movement
#     '''
#
#     type = None
#     _Walk = 0
#     _Land = 1
#     _Hoover = 2
#     #self._Swim = 3
#     #self._Jump = 4
#
#     def __init__(self, type):
#         self.type = type


class GroundUnit(Unit):

    def __init__(self, settings, model, agentName, layer, uniqInMap=True):
        super(GroundUnit, self).__init__(settings, model, agentName, layer, uniqInMap)
        self.movement = _LAND
        self.properties._unitType = _GROUND


class HooverUnit(Unit):

    def __init__(self, settings, model, agentName, layer, uniqInMap=True):
        super(HooverUnit, self).__init__(settings, model, agentName, layer, uniqInMap)
        self.movement = _AIR
        self.properties._unitType = _HOOVER


class InfantryUnit(Unit):

    def __init__(self, settings, model, agentName, layer, uniqInMap=True):
        super(InfantryUnit, self).__init__(settings, model, agentName, layer, uniqInMap)
        self.movement = _WALK
        self.properties._unitType = _INFANTRY


class HumanSquad(InfantryUnit):

    def __init__(self, settings, model, agentName, layer, uniqInMap=True):
        super(HumanSquad, self).__init__(settings, model, agentName, layer, uniqInMap)

        self.properties._cost = 20
        self.properties._maxAP = 70
        self.properties._maxHealth = 10
        self.properties._upkeep = 1
        self.properties._faction = "Human"
        self.properties._unitName = "Squad"

        self.properties.initialize()

        self.lightWeapon = Gun(self.world,fireRate= 20, damageContact=10, range = 5)
