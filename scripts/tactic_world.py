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
from world import *

from gui.huds import TacticalHUD
from combat import Trajectory
from scripts.tactic_scene import TacticScene




class TacticListener(WorldListener):
    """
    Main game listener.  Listens for Mouse and Keyboard events.

    This class also has the ability to attach and detach itself from
    the event manager in cases where you do not want input processed (i.e. when
    the main menu is visible).  It is NOT attached by default.
    """

    def __init__(self, world):
        super(TacticListener, self).__init__(world)


    def clickAttack(self, clickpoint):
        '''
        Handles the click action when attack is selected.
        :return:
        '''

        if not self._world.activeUnit:
            print "No active unit selected!"
            return

        clickLocation = self._world.getLocationAt(clickpoint)
        trajectory = Trajectory(self._world.scene.instance_to_agent[self._world.activeUnit], self._world,0)
        # print "Is is reachable?"
        if trajectory.isInRange(clickLocation):

        # print "Calculating Clear path:"
            if trajectory.hasClearPath(clickLocation):
                self._world.scene.instance_to_agent[self._world.activeUnit].attack(clickLocation)


    def clickDefault(self, clickpoint):
        # self.hide_instancemenu()

        instances = self._world.getInstancesAt(clickpoint)
        print "selected instances on agent layer: ", [i.getObject().getId() for i in instances]
        print "Found " , instances.__len__(), "instances"

        if instances:
            # self.activeUnit = None
            print "Current turn:" , self._world.scene.currentTurn
            for instance in instances:
                id = instance.getFifeId()
                print "Instance: ", id
                print "Is it in: ", self._world.scene.factionUnits[self._world.scene.currentTurn]
                if id in self._world.scene.factionUnits[self._world.scene.currentTurn]:
                    print "Instance: " , id, " is owned by this player!"
                    #self.activeUnit = id
                    self._world.selectUnit(id)

        elif self._world.activeUnit:
            # there was a unit selected and an empty cell has been clicked
            agent = self._world.scene.instance_to_agent[self._world.activeUnit]
            if agent.agentType == "Unit" and not self._world.busy:
                # move the unit if possible
                self._world.scene.instance_to_agent[self._world.activeUnit].run(self._world.getLocationAt(clickpoint))
            else:
                # we assume it's a building -> deselect it.
                self._world.selectUnit(None)


    def clickDeploy(self, clickpoint):
        '''
        Specific deploying behavior for tactic situations: Units can only be deployed right next to the building.
        '''
        unit = self._world.deploying
        buildingID = self._world.activeUnit
        building = self._world.scene.instance_to_agent[buildingID]

        ## Get center point of the building.
        buildingLocation = building.agent.getLocation()

        clickLocation = self._world.getLocationAt(clickpoint)
        layer = buildingLocation.getLayer()
        cellCache = layer.getCellCache()
        clickCell = cellCache.getCell(clickLocation.getLayerCoordinates())

        properties = building.properties

        canTeleport = False

        for x in range(properties["SizeX"]):
            for y in range(properties["SizeY"]):
                cellPos = buildingLocation.getLayerCoordinates()
                cellPos.x -= x
                cellPos.y -= y

                cell = cellCache.getCell(cellPos)
                if clickCell.isNeighbor(cell):
                    canTeleport = True
                    break

            if canTeleport:
                break

        ## TODO: Give feedback!
        if not canTeleport:
            self.cancelDeploy()
            return

        if not unit.teleport(clickLocation):
            # This is supposed to be an ilegal teleport position -> cancel
            self.cancelDeploy()
            return

        # Generate an instance for the unit.
        unit.createInstance(clickLocation)
        # unit.teleport(clickLocation)
        instanceID = unit.agent.getFifeId()
        self._world.scene.instance_to_agent[instanceID] = unit
        faction = unit.properties["faction"]
        self._world.scene.factionUnits[faction].append(instanceID)
        self._world.cellRenderer.addPathVisual(unit.agent)
        self._world.storage.unitDeployed()
        self.cancelDeploy()


    def mouseMoved(self, evt):
        '''
        Display feedback of the movement range of the unit
        :return:
        '''

        unitID = self._world.activeUnit

        if not unitID:
            super(TacticListener, self).mouseMoved(evt)
            return

        unit = self._world.scene.instance_to_agent[unitID]
        if unit.agentType != "Unit": # It's a building
            super(TacticListener, self).mouseMoved(evt)
            return

        self._world.mousePos = (evt.getX(), evt.getY())
            ## If we reached this point we should show the maximum range of the movement.

        ## TODO: Make this a path object for convenience.
        ## TODO: Make a separate thread for this perhaps?

        if self._world.mode == self._world.MODE_DEFAULT:

            mousePoint = fife.ScreenPoint(evt.getX(), evt.getY())
            location = self._world.getLocationAt(mousePoint)

            iPather = fife.RoutePather()
            route = iPather.createRoute(unit.agent.getLocation(), location, False)
            route.setObject(unit.agent.getObject())
            iPather.solveRoute(route, fife.HIGH_PRIORITY,True)
            movesLeft = unit.AP / 10
            route.cutPath(movesLeft) ## Cut the path short if too long
            self._cellSelectionRenderer.reset()
            while not route.reachedEnd():
                node = route.getNextNode()
                if not route.walkToNextNode():
                    break
                self._cellSelectionRenderer.selectLocation(node)



    def clickGetIn(self, clickpoint):
        # self.hide_instancemenu()

        if not self._world.activeUnit:
            return
        else:
            activeUnit = self._world.scene.instance_to_agent[self._world.activeUnit]
            if activeUnit.agentType == "Building":
                return

        instances = self._world.getInstancesAt(clickpoint)
        print "selected instances on agent layer: ", [i.getObject().getId() for i in instances]
        print "Found " , instances.__len__(), "instances"

        if instances:
            # self.activeUnit = None
            for instance in instances:
                id = instance.getFifeId()
                print "Instance: ", id
                if id in self._world.scene.instance_to_agent.keys():
                    clickedAgent = self._world.scene.instance_to_agent[id]
                    if clickedAgent.properties["faction"] != self._world.scene.currentTurn:
                        return
                    if clickedAgent.agentType == "Building":
                        storage = clickedAgent.storage
                        if storage:
                            ##HACK: only accept on dropships
                            if clickedAgent.properties["StructureCategory"] == "Dropship":
                                if self.canGetToPerimeter(activeUnit, clickedAgent):
                                    if storage.addUnit(activeUnit):
                                        ## storage added correctly -> remove unit from the map.
                                        activeUnit.die()
                                        self._world.selectUnit(None)


    def canGetToPerimeter(self, activeUnit, building):
        '''
        Checks if the active unit is able to move itself to the perimeter of the building in order to be included.
        :param activeUnit: A unit that wants to get inside a building
        :param clickedAgent: Building that can accept the activeUnit.
        :return:
        '''
        buildingLocation = building.agent.getLocation()

        startingPos = buildingLocation.getMapCoordinates()

        iPather = fife.RoutePather()
        movesLeft = activeUnit.AP / 10

        for x in range(-1 , building.properties["SizeX"] +1):
            for y in range(-1 , building.properties["SizeY"]+1):
                cellPos = fife.DoublePoint3D(startingPos)
                cellPos.x -= x
                cellPos.y -= y

                loc = fife.Location(buildingLocation)
                loc.setMapCoordinates(cellPos)

                route = iPather.createRoute(activeUnit.agent.getLocation(), loc, False)
                route.setObject(activeUnit.agent.getObject())
                iPather.solveRoute(route, fife.HIGH_PRIORITY,True)
                routeLength = route.getPathLength()
                if routeLength < 1:
                    print "Route length: " , routeLength
                    continue
                if movesLeft >= (routeLength-1):
                    return True
        ## TODO: give feedback.
        return False







class TacticWorld(World):
    """
    The world!

    This class handles:
      setup of map view (cameras ...)
      loading the map

    That's obviously too much, and should get factored out.
    """
    def __init__(self, universe, planet):
        super(TacticWorld, self).__init__(universe, planet)

        self._nextTurnWindow = None


        self.listener = TacticListener(self)
        self.listener.attach()

        self.faction = self.universe.faction

        self.scene = TacticScene(self, self.engine)

        self.HUD = TacticalHUD(self)
        self.HUD.show()


    def onAttackButtonPressed(self):
        if self.activeUnit:
            self.setMode(self.MODE_ATTACK)


    def startDeploy(self, storage):
        self.storage = storage
        self.setMode(self.MODE_DEPLOY)
        building = self.scene.instance_to_agent[self.activeUnit]
        properties = building.properties

        ## Show the available cells:
        buildingLocation = building.agent.getLocation()
        self.listener._cellSelectionRenderer.reset()

        startingPos = buildingLocation.getMapCoordinates()

        for x in range(-1 , properties["SizeX"] +1):
            for y in range(-1 , properties["SizeY"]+1):
                cellPos = fife.DoublePoint3D(startingPos)
                cellPos.x -= x
                cellPos.y -= y

                loc = fife.Location(buildingLocation)
                loc.setMapCoordinates(cellPos)

                self.listener._cellSelectionRenderer.selectLocation(loc)

