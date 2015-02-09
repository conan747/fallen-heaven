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
from building import Building





## TODO: When unit is moving, prevent from selecting new position.

class Unit(Agent):
    '''
    ;Unit Type name
    ;Facing ID (BMP file)
    ;Name of light weapon section or NO WEAPON
    ;Name of heavy weapon section
    ;Type of movement "NOMOVE", "GROUND", "HOVER"
    ;Cash to produce
    ;Type of industry producing it "NONE", "TROOP", "FACTORY", "HOVER", "MISSILE", "DROPSHIP"
    ;Action Points
    ;Armor
    ;Upkeep cost
    ;Unit Type Category Squad, SuperSquad, Buggy, LtGrav, LtTank, Tank, HeavyGrav,
    ;                   LongRange, LongRangeHover, MegaTank, TowerGun,
    ;					Dropship, NuclearMissile
    ;MoveSound			(Troop, Wheeled, Tracked, Hovering)
    ;Embedded			--> Only used for Towers, optionnal field --> TRUE / FALSE
    ;EncyclopediaImg	--> Image to display in the encyclopedia
'''

    WALK, LAND, AIR = xrange(3)
    INFANTRY, GROUND, HOOVER = xrange(3)
    LWEAPON, HWEAPON = xrange(2)

    instance = None

    # movement = None
    lightWeapon = None
    heavyWeapon = None
    AP = None

    def __init__(self, world, properties, lWeapon = None, HWeapon = None):

        super(Unit, self).__init__(properties["unitName"], "Unit", world)
        self.agentType = "Unit"
        self.properties = properties

        self.health = self.properties["Hp"]
        self.AP = self.properties["TimeUnits"]




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
        self.AP = self.properties["TimeUnits"]

    def teleport(self, location):
        print "Teleportin unit"
        exactcoords = location.getLayerCoordinates()
        layercoords = fife.DoublePoint3D(int(exactcoords.x), int(exactcoords.y), int(exactcoords.z) )
        location.setExactLayerCoordinates(layercoords)

        # if layercoords == self.agent.get

        ## TODO: Handle the teleport looking if the target cell is not occupied and the unit can stand there (e.g. not water).
        if not self.world.scene.getInstacesInTile(location):
            if self.agent:
                self.agent.setLocation(location)
            print "It was able to teleport"
            return True
        print "Not able to teleport!"
        return False


    def run(self, location):

        # if not self._renderer:
        #     self._renderer = fife.CellSelectionRenderer.getInstance(self.world.cameras['main'])

        # self._renderer.setEnabled(False)
        # self.state = _STATE_RUN
        movesLeft = self.AP / 10

        iPather = fife.RoutePather()
        route = iPather.createRoute(self.agent.getLocation(),location, True)
        route.cutPath(movesLeft) ## Cut the path short if too long
        self.AP -= route.getPathLength() *10
        print "Path length:", route.getPathLength()

        self.agent.move('stand', route.getEndNode(), 5)


    def die(self):
        print "This unit is dead!"
        self.world.scene.unitDied(self.agent.getFifeId())
        # self.layer.deleteInstance(self.agent)



    def attack(self, location, weaponType=None):
        if not weaponType:
            weaponType = self.LWEAPON
        if weaponType == self.LWEAPON:
            self.lightWeapon.fire(location)
        elif weaponType == self.HWEAPON:
            self.heavyWeapon.fire(location)





class Weapon(object):
    """
    Weapon

    """

    def __init__(self, world):
        self._world = world
        self.properties = {}



    def fire(self, location):
        """
        Fires the weapon in the specified direction.
        To be rewritten
        """
        self._world.scene.applyDamage(location, self.properties["DamageContact"])
