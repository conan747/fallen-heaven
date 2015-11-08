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



class Projectile(fife.InstanceActionListener):
    
    def __init__(self, world, origin, destination):

        super(Projectile, self).__init__()

        self.start = False
        self.world = world
        ## Show projectile
        # self.layer = origin.getLayer()
        self.layer = world.scene.map.getLayer("TrajectoryLayer")
        self.layer.setWalkable(True)

        object = world.model.getObject("SBT", "fallen")
        object.addWalkableArea("land")
        object.setBlocking(False)
        print "Attacking from: " , origin.getLayerCoordinates()
        originCoords = origin.getExactLayerCoordinates()
        originCoords.x +=1
        originCoords.y +=1
        self.instance = self.layer.createInstance(object, originCoords)
        self.instance.addActionListener(self)
        self.visual = fife.InstanceVisual.create(self.instance)
        self.visual.setVisible(True)
        self.instance.setCellStackPosition(0)
        self.destination = fife.Location(self.layer)
        self.destination.setLayerCoordinates(destination.getLayerCoordinates())
        print "To: ", self.destination.getLayerCoordinates()
        print "\n\nbullet created!"
        self.move()

    def move(self):
        #self.world.busy = True
        if self.destination.isValid():
            self.instance.move("move", self.destination, 5)
            self.start = True

    def onInstanceActionFinished(self, instance, action):
        print action.getId()
        if action.getId() == "move" and self.start:
            print "\n\nDestroying bullet"
            self.instance.removeActionListener(self)
            self.visual.setVisible(False)
            #self.world.busy = False
            #self.layer.deleteInstance(self.instance)


    def onInstanceActionCancelled(self, instance, action):
        print "Action cancelled!"

    def onInstanceActionFrame(self, instance, action, frame):
        print "Action frame" , frame


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
        # activeUnitLocation = self.world.scene.instance_to_agent[self.world.activeUnit].getLocation()
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

        if runAfterFinish:
            runAfterFinish()


    def die(self):
        print "This unit is dead!"
        self.world.scene.unitDied(self.instance.getFifeId())
        # self.layer.deleteInstance(self.agent)



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

            weapon.fire(location)

            self.projectile = Projectile(self.world ,self.instance.getLocation(), location)

            # Reduce APs
            percentTimeUnits = weapon.properties["PercentTimeUnits"]
            deducing = percentTimeUnits * self.properties["TimeUnits"] / 100
            self.AP -= deducing

        else:
            print "Not enough APs!"
            self.playError()

        #TODO: manage weapon choosing.

        # if not weaponType:
        #
        # if weaponType == self.LWEAPON:
        #     self.lightWeapon.fire(location)
        # elif weaponType == self.HWEAPON:
        #     self.heavyWeapon.fire(location)




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
        self._world.scene.applyDamage(location, self.properties["DamageContact"])

