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
from combat import *




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

        activeAgent = self._world.getActiveAgent()
        clickLocation = self._world.getLocationAt(clickpoint)
        trajectory = Trajectory(activeAgent , self._world, self._world.attackType)
        # print "Is is reachable?"
        if trajectory.isInRange(clickLocation):
            # print "Calculating Clear path:"
            if trajectory.hasClearPath(clickLocation):
                activeAgent.attack(clickLocation, self._world.attackType)
                self._world.HUD.updateUI()


    def clickDefault(self, clickpoint):
        # self.hide_instancemenu()

        instances = self._world.getInstancesAt(clickpoint)

        if instances:
            self.cycleThroughInstances(instances)
            print "selected instances on agent layer: ", [i.getObject().getId() for i in instances]
            print "Found " , instances.__len__(), "instances"

        elif self._world.activeUnit:
            # there was a unit selected and an empty cell has been clicked

            agent = self._world.getActiveAgent()
            if agent.agentType == "Unit" and not self._world.busy:
                # move the unit if possible
                location = self._world.getLocationAt(clickpoint)
                if agent.canTeleportTo(location):
                    agent.run(location, self._cellSelectionRenderer.reset)
                else:
                    agent.playError()
            else:
                # we assume it's a building -> deselect it.
                self._world.selectUnit(None)


    def clickDeploy(self, clickpoint):
        '''
        Specific deploying behavior for tactic situations: Units can only be deployed right next to the building.
        '''

        unit = self._world.deploying
        building = self._world.getActiveAgent()

        ## Get center point of the building.
        buildingLocation = building.instance.getLocation()

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
        instanceID = unit.instance.getFifeId()
        faction = unit.properties["faction"]
        self._world.factionUnits[faction].append(instanceID)
        self._world.view.addPathVisual(unit.instance)
        self._world.storage.unitDeployed()
        self.cancelDeploy()


    def mouseMoved(self, evt):
        '''
        Display feedback of the movement range of the unit
        :return:
        '''

        if not self.unitManager:
            self.unitManager = self._world.unitManager

        unit = self._world.getActiveAgent()

        if not unit:
            super(TacticListener, self).mouseMoved(evt)
            return

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

            # See if the unit could possibly move to this location due to the cell type.
            # If it can't move, then we don't need to calculate or draw the path.
            if not unit.canTeleportTo(location):
                self._cellSelectionRenderer.reset()
                return

            iPather = fife.RoutePather()
            route = iPather.createRoute(unit.instance.getLocation(), location, False)
            route.setObject(unit.instance.getObject())
            iPather.solveRoute(route, fife.HIGH_PRIORITY,True)
            movesLeft = unit.AP / 10
            route.cutPath(movesLeft) ## Cut the path short if too long
            self._cellSelectionRenderer.reset()
            while not route.reachedEnd():
                node = route.getNextNode()
                if not route.walkToNextNode():
                    break
                self._cellSelectionRenderer.selectLocation(node)

        #elif self._world.mode == self._world.MODE_ATTACK:




    def clickGetIn(self, clickpoint):
        # self.hide_instancemenu()

        if not self._world.activeUnit:
            return

        if not self.unitManager:
            self.unitManager = self._world.unitManager
        activeUnit = self._world.getActiveAgent()
        if activeUnit.agentType == "Building":
            return

        instances = self._world.getInstancesAt(clickpoint)
        print "selected instances on agent layer: ", [i.getObject().getId() for i in instances]
        print "Found " , instances.__len__(), "instances"

        for instance in instances:
                clickedAgent = self.unitManager.getAgent(instance)
                if not clickedAgent or clickedAgent.properties["faction"] != self._world.currentTurn:
                        return
                if clickedAgent.agentType == "Building":
                    storage = clickedAgent.storage
                    if storage:
                        ##HACK: only accept on dropships
                        if clickedAgent.properties["StructureCategory"] == "Dropship":
                            if self.canGetToPerimeter(activeUnit, clickedAgent):
                                if storage.addUnit(activeUnit):
                                    ## storage added correctly -> remove unit from the map.
                                    activeUnit.die() #TODO: This shouldn't be die.
                                    self._world.selectUnit(None)


    def canGetToPerimeter(self, activeUnit, building):
        '''
        Checks if the active unit is able to move itself to the perimeter of the building in order to be included.
        :param activeUnit: A unit that wants to get inside a building
        :param clickedAgent: Building that can accept the activeUnit.
        :return:
        '''
        buildingLocation = building.instance.getLocation()

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

                route = iPather.createRoute(activeUnit.instance.getLocation(), loc, False)
                route.setObject(activeUnit.instance.getObject())
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

        self.listener = TacticListener(self)
        self.listener.attach()


        playerFactionName = self.universe.progress.playerFactionName
        self.currentTurn = playerFactionName
        self.factionNames = [playerFactionName, "Tauran"]

        #GUI
        self._nextTurnWindow = None
        self.HUD = TacticalHUD(self)
        self.HUD.show()

        self.combatManager = CombatManager(self)


    def pump(self):
        super(TacticWorld, self).pump()
        self.projectileGraveyard = ProjectileGraveyard(self.view.layers["TrajectoryLayer"], self.combatManager)
        self.combatManager.next()


    def load(self, filename):
        super(TacticWorld, self).load(filename)

        ## Start cellRenderer to show instance paths:
        self.view.setVisual(self.unitManager.getAgents())

        # Setup factionUnits
        for factionName in self.factionNames:
            self.factionUnits[factionName] = []
            for agent in self.unitManager.getAgents():
                if agent.properties["faction"] == factionName:
                    self.factionUnits[factionName].append(agent.getFifeId())

        self.selectUnit(None)


    def resetAPs(self):
        '''
        Resets the AP points of all the units to its maximum.
        '''
        for unitID in self.factionUnits[self.currentTurn]:
            print "Reseting: ", unitID
            unit = self.unitManager.getAgent(unitID)
            unit.resetAP()


    def nextTurn(self):
        '''
        Skips to the next turn
        '''
        if self.factionNames[0] == self.currentTurn:
            self.currentTurn = self.factionNames[1]
        else:
            self.currentTurn = self.factionNames[0]
        self.selectUnit(None)
        self.resetAPs()
        self.setMode(self.MODE_DEFAULT)
        ## TO-DO: add a message stating who's turn it is.
        # print self.instance_to_agent
        # for key in self.instance_to_agent.keys():
        #     instance = self.instance_to_agent[key]
        #     instance.runTurn()



    def applyDamage(self, location, damage):
        '''
        Deals damage to a specific location (and all the units within).
        :param location: Place where the damage is applied in the map.
        :param damage: Ammount of damage dealt
        :return:
        '''
        targetIDs = self.getInstancesAt(location)
        for unitID in targetIDs:
            agent = self.unitManager.getAgent(unitID)
            print "Dealt %s damage to %s" % (damage, agent.instance.getId())
            agent.getDamage(damage)



    def unitDied(self, unitID, explode=False):
        '''
        Process the destruction of a unit
        :param unitID: ID of the destroyed unit
        :return:
        '''
        if self.activeUnit == unitID:
            self.selectUnit(None)
            self.setMode(self.MODE_DEFAULT)

        self.unitGraveyard.add(self.unitManager.getAgent(unitID).instance, explode)

        self.unitManager.removeInstance(unitID, explode)


    def reset(self):
        ### TODO This should be fixed!!!
        pass


    def onAttackButtonPressed(self, attackType):
        if self.activeUnit:
            self.attackType = attackType
            self.setMode(self.MODE_ATTACK)
            self.HUD.updateUI()
        else:
            pass
            # TODO: Reproduce error sound.


    def startDeploy(self, storage):
        self.storage = storage
        self.setMode(self.MODE_DEPLOY)
        if not self.unitManager:
            self.unitManager = self._world.unitManager
        building = self.getActiveAgent()
        properties = building.properties

        ## Show the available cells:
        buildingLocation = building.instance.getLocation()
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

