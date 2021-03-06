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
import random


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
        #TODO: Idea: sniper tower!

    # WALK, LAND, AIR = xrange(3)
    # INFANTRY, GROUND, HOOVER = xrange(3)
    LWEAPON, HWEAPON = xrange(2)


    def __init__(self, world, properties, lWeapon = None, HWeapon = None):

        super(Unit, self).__init__(properties["unitName"], "Unit", world)
        self.agentType = "Unit"
        self.properties = properties

        self.instance = None

        self.health = self.properties["Hp"]
        self.AP = self.properties["TimeUnits"]

        self.speaker = self.world.universe.sound.playFX

        if lWeapon:
            self.lightWeapon = lWeapon
        if HWeapon:
            self.heavyWeapon = HWeapon

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
        self.AP = self.properties["TimeUnits"]


    def canTeleportTo(self, location):
        '''
        Tells if the location would be legal for this unit.
        :param location:
        :return: Boolean
        '''
        layer = location.getLayer()
        cellCache = layer.getCellCache()
        cellPos = location.getLayerCoordinates()

        if layer.cellContainsBlockingInstance(cellPos):
            return False
        if self.properties["Movement"] == "GROUND":
            cell = cellCache.getCell(cellPos)
            if cellCache.isCellInArea("water", cell):
                return False

        return True

    def playError(self):
        self.speaker("error")

    def teleport(self, location):
        print "Teleporting unit"

        # Check if we are pointing at the same location as the current unit.
        # activeUnitLocation = self.world.instance_to_agent[self.world.activeUnit].getLocation()
        # if activeUnitLocation == location:
        #     return True

        if not self.canTeleportTo(location):
            self.playError()
            return False

        if not self.world.cameras['main'].getMatchingInstances(location, False):
            if self.instance:
                self.instance.setLocation(location)
            print "It was able to teleport"
            return True
        print "Not able to teleport!"

        self.playError()
        return False


    def run(self, location, runAfterFinish=None):
        '''
        Moves the unit "legally" to the selected position. After it ends, it runs "runAfterFinish" command.
        :param location:  Location
        :param runAfterFinish: Command to be run after finish
        :return: None
        '''
        # if not self._renderer:
        #     self._renderer = fife.CellSelectionRenderer.getInstance(self.world.cameras['main'])

        # self._renderer.setEnabled(False)
        # self.state = _STATE_RUN
        movesLeft = self.AP / 10

        iPather = fife.RoutePather()
        route = iPather.createRoute(self.instance.getLocation(),location, False)
        route.setObject(self.instance.getObject())
        iPather.solveRoute(route, fife.HIGH_PRIORITY,True)
        route.cutPath(movesLeft) ## Cut the path short if too long
        pathLength = route.getPathLength()-1
        if pathLength > 0:
            self.AP -= pathLength * 10
            print "Path length:", route.getPathLength()-1
            self.world.busy = True
            self.instance.move('stand', route.getEndNode(), 5)

        if self.world.combatRecorder:
            self.world.combatRecorder.onMoved(self, location)

        if runAfterFinish:
            runAfterFinish()


    def die(self, explode=False):
        print "This unit died!"

        self.instance.removeActionListener(self)
        self.world.unitDied(self.instance.getFifeId(), explode=explode)



    def canAttack(self, weaponType):
        '''
        Returns if the unit has enough APs to attack.
        :param weaponType:  int: either LWEAPON OR HWEAPON
        :return:
        '''

        if weaponType == self.LWEAPON:
            percentTimeUnits = self.lightWeapon.properties["PercentTimeUnits"]
        else:
            percentTimeUnits = self.heavyWeapon.properties["PercentTimeUnits"]

        percentageRemaining = self.AP * 100 / self.properties["TimeUnits"]
        if percentTimeUnits <= percentageRemaining:
            return True
        else:
            return False

    def attack(self, location, weaponType=None):

        ## TODO: add self.instance.setFacingLocation

        if weaponType == self.LWEAPON:
            weapon = self.lightWeapon
        else:
            weapon = self.heavyWeapon

        if self.canAttack(weaponType):

            location = self.computePrecision(weapon, location)

            # Signal the combatManager
            self.world.combatManager.newCombat(self)
            self.shoot(location, weaponType)

            # Reduce APs
            percentTimeUnits = weapon.properties["PercentTimeUnits"]
            deducing = percentTimeUnits * self.properties["TimeUnits"] / 100
            self.AP -= deducing

        else:
            print "Not enough APs!"
            self.playError()

    def shoot(self, realLocation, weaponType):
        '''
        Preforms a shot at the location without computing precision. It should be called from attack or combatPlayer.attack()
        :param realLocation: Location where the projectile will travel.
        :param weapon: The weapon that was used.
        :return:
        '''
        if weaponType == self.LWEAPON:
            weapon = self.lightWeapon
        else:
            weapon = self.heavyWeapon


        def callback(func = self.afterAttack, weapon= weapon, location = realLocation):
                func(weapon, location)

        self.world.combatManager.addProjectile(self.instance.getLocation(), realLocation, weapon=weapon, callback=callback)
        if self.world.combatRecorder:
            self.world.combatRecorder.onAttack(self, realLocation, weaponType)


        # Reduce APs # Activate this if necessary.
        if False:
            percentTimeUnits = weapon.properties["PercentTimeUnits"]
            deducing = percentTimeUnits * self.properties["TimeUnits"] / 100
            self.AP -= deducing


    def afterAttack(self, weapon, location):
        weapon.fire(location)

        if self.world.combatPlayer:
            self.world.combatPlayer.carryOn()

    def computePrecision(self, weapon, location):
        '''
        Gives the location of the attack depending on the precision.
        :param weapon: The weapon that has been shot
        :param location: The intended location
        :return: The new location.
        '''
        precision = weapon.properties["Precision"]
        failProbability = 10 + precision
        diceRoll = random.randint(0,99)
        if failProbability >= diceRoll:
            newLocation = fife.Location(location.getLayer())
            locationCoords = location.getLayerCoordinates()
            shift = [0,0]
            while shift == [0,0]:
                shift[0] = random.randint(-1,1)
                shift[1] = random.randint(-1,1)
            locationCoords.x += shift[0]
            locationCoords.y += shift[1]
            newLocation.setLayerCoordinates(locationCoords)

            print "Target missed!"
            return newLocation
        else:
            return location


class Weapon(object):
    """
    Weapon
    ------

    Name=EXPLOSIVE MINE
    Parabolic=0
    Display=S-CLOSEATTACK
    Turreted=1
    Range=1
    Precision=-2
    DamageContact=30
    DamageClose=0
    DamageFar=0
    PercentTimeUnits=60
    """

    def __init__(self, world):
        self._world = world
        self.properties = {}
        self.speaker = self._world.universe.sound.playFX

    def fire(self, location):
        """
        Fires the weapon in the specified direction.
        """
        #Handle animation
        self.speaker("explosion")

        self._world.applyDamage(location, self.properties["DamageContact"])

        if self.properties["DamageClose"] > 0:
            # Compute damage close:
            tempLocation = fife.Location(location.getLayer())

            for y in range(-1, 2):
                for x in range(-1,2):
                    if not  (x or y):
                        continue
                    cellPos = location.getLayerCoordinates()
                    cellPos.x -= x
                    cellPos.y -= y
                    tempLocation.setLayerCoordinates(cellPos)
                    self._world.applyDamage(tempLocation, self.properties["DamageClose"])

            if self.properties["DamageFar"] > 0:
                # Compute damage close:
                tempLocation = fife.Location(location.getLayer())
                layer = location.getLayer()

                for y in (-2, 2):
                    cellPos = location.getLayerCoordinates()
                    cellPos.y -= y
                    tempLocation.setLayerCoordinates(cellPos)
                    self._world.applyDamage(tempLocation, self.properties["DamageFar"])

                for x in (-2, 2):
                    cellPos = location.getLayerCoordinates()
                    cellPos.x -= x
                    tempLocation.setLayerCoordinates(cellPos)
                    self._world.applyDamage(tempLocation, self.properties["DamageFar"])

