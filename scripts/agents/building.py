# -*- coding: utf-8 -*-

# ####################################################################
# Copyright (C) 2005-2013 by the FIFE team
# http://www.fifengine.net
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
from fife.extensions import pychan
from fife.extensions.pychan import widgets
from scripts.gui.selectPlanet import SelectPlanet

import uuid



class Storage(object):
    '''
    This class will handle units inside a building/dropship. Also, it will handle units being produced.
    '''



    # typeDict = {"NONE" : "None"
    #     , "TROOP"
    #     , "FACTORY"
    #     , "HOVER"
    #     , "MISSILE"
    #     , "DROPSHIP"}

    def __init__(self, building, world):
        self.parent = building

        self.ableToProduce = []  # Contains the unit names of the units that can be produced in this building
        self.unitsReady = []  # List containing the unitID that are ready to be deployed.
        self.inProduction = []  # List of names containing the units that have been "bought" but they are in production.

        # if self.parent.agent:
        #     self.parentID = building.instance.getFifeId()  # Parent ID of the object that contains this storage.
        self.world = world

        # Get the units that this is able to produce:
        productionType = self.parent.properties["ProductionType"]
        if productionType != "NONE":
            unitList = self.world.unitLoader.unitProps
            self.ableToProduce = []

            for unitName in unitList:
                if unitList[unitName]["ProductionType"] == productionType:
                    if unitList[unitName]["faction"] == self.parent.properties["faction"]:
                        self.ableToProduce.append(unitName)

            print "Units able to be produced by this building: ", productionType
            print self.ableToProduce

        self.deployingID = None

        self.updateUI = self.world.HUD.updateUI
        self.storageSize = self.parent.properties["StorageSize"]


    def setStorage(self, infoDict):
        '''
        Sets the storage info that was loaded from the progress.
        :param infoDict: Dictionary containing two lists: unitsReady and inProduction
        :return:
        '''
        if not infoDict:
            return

        for key in infoDict.keys():
            setattr(self, key, infoDict[key])

    def cancelUnit(self, unitName):
        print "Removing: ", unitName
        self.inProduction.remove(unitName)
        unitName = unitName.split(":")[1]
        cost = int(self.world.unitLoader.unitProps[unitName]["Cost"])
        self.world.deductCredits(-cost)
        self.updateUI()


    def buildUnit(self, unitName):
        print "Building ", unitName

        cost = int(self.world.unitLoader.unitProps[unitName]["Cost"])
        if self.world.deductCredits(cost):

            # Create an icon for the new unit:
            prefix = uuid.uuid4().int
            iconName = str(prefix)+':'+ unitName
            self.inProduction.append(iconName)

            self.updateUI()

        else:
            print "Not enough Credits!"

    def addUnit(self, unit, iconName=None):
        '''
        Adds a unit into this storage.
        :param unit: Unit object to be added.
        :return: iconName if it succedes, else False.
        '''
        #TODO: Check if this storage accepts this units.
        if len(self.unitsReady) == self.storageSize:
            print "Storage is full!"
            return False
            ## Give feedback of why it didn't work!
        if not iconName:
            unitName = unit.agentName
            prefix = uuid.uuid4().int
            iconName = str(prefix)+':'+ unitName
        self.unitsReady.append(iconName)
        self.updateUI()
        return iconName



    def completeUnits(self):
        '''
        This command makes units in production be completed.
        :return:
        '''
        print "Running completeConstruction"
        for unit in self.inProduction:
            self.unitsReady.append(unit)

        self.inProduction = []
        self.updateUI()

    def deployUnit(self, unitID):
        '''
        Start deploy mode.
        :param unitName:
        :return:
        '''
        print "Deploying unit" , unitID
        self.world.startDeploy(self)
        # self.world.setMode(self.world.MODE_DEPLOY)
        # self.world.storage = self
        unitName = unitID.split(":")[1]
        unit = self.world.unitLoader.createUnit(unitName)
        self.world.deploying = unit
        self.deployingID = unitID
        print "Deploying unit", unitName


    def unitDeployed(self, unitName=None):
        if not unitName:
            unitName = self.deployingID
        self.unitsReady.remove(unitName)

        self.deployingID = None
        self.updateUI()

    def getStorageDict(self):
        '''
        Returns a dictionary containing units in storage.
        :return:
        '''
        thisStorage = {"inProduction" : self.inProduction,
                                       "unitsReady" : self.unitsReady}
        return thisStorage

class DummyInstance(fife.Instance):
    '''
    Dummy instance to fill up the empty cells on a building. It will refer to the parent building.
    '''

    @staticmethod
    def getDummyObject():
        obj = fife.Object("dummy", "fallen")
        obj.setBlocking(True)
        obj.setStatic(True)
        return obj

    def __init__(self, parent, location):

        #obj = self.getDummyObject()
        self._parent = parent
        obj = self._parent.world.model.getObject("dummy", "fallen")
        self.parentID = self._parent.instance.getFifeId()
        identifier = "dummy_%s" % self.parentID
        #point = location.getLayerCoordinates()
        super(DummyInstance, self).__init__(obj, location, identifier)
        self.instanceVisual = fife.InstanceVisual.create(self)


    def getParentAgent(self):
        return self._parent

    def getFifeId(self):
        self.parentID

    # def getId(self):
    #     return "dummy"

class Building(Agent):


    landed = False


    def __init__(self, world, props):

        super(Building, self).__init__(props["unitName"], "Building", world)
        self.agentType = "Building"
        self.properties = props


        # self.agent = layer.getInstance(agentName)
        self._renderer = None
        self._SelectRenderer = None
        self.cellCache = None
        self.storage = None
        self.action = None # Points to a method. It is used when the building can perform an action.
        ## HACK: I don't create the storage now but when the building is landed. It's better for memory purposes.
        # if self.properties["ProductionType"] != "NONE":
        #     self.storage = Storage(self, self.world)

        ## If it is a special building, then link its action:
        actionMap = {"Dropship" : self._takeoff,
                     "STARPORT" : self._buildDropship}

        if props["StructureCategory"] in actionMap.keys():
            self.action = actionMap[props["StructureCategory"]]

        self.health = self.properties["Hp"]

        self.dummyInstances=[]

    def createInstance(self, location):
        '''
        We should remove the blocking flag.
        :param location:
        :return:
        '''
        super(Building, self).createInstance(location)
        self.instance.setBlocking(False)

    def selectInstance(self, instanceName):
        '''
        We should remove the blocking flag.
        :param instanceName:
        :return:
        '''
        super(Building, self).selectInstance(instanceName)
        self.instance.setBlocking(False)


    def calculateDistance(self, location):
        iPather = fife.RoutePather()
        route = iPather.createRoute(self.instance.getLocation(), location, True)
        distance = route.getPathLength()
        return distance


    def teleport(self, location):
        '''
        Teleports the instance to the location if possible
        :param location: Location to which it should be teleported.
        :return: Boolean indicated if it could teleport.
        '''
        if self.landed:
            print "Can't teleport! Already constructed here!"
            return False

        exactcoords = location.getLayerCoordinates()
        layercoords = fife.DoublePoint3D(int(exactcoords.x), int(exactcoords.y), int(exactcoords.z))
        location.setExactLayerCoordinates(layercoords)

        if location == self.instance.getLocation():
            return True


        layer = self.instance.getLocation().getLayer()
        cellCache = layer.getCellCache()

        # unblocked = True
        for x in range(self.properties["SizeX"]):
            for y in range(self.properties["SizeY"]):
                # if (x or y) == 0:
                #     continue
                # loc = self.instance.getLocation()
                cellPos = location.getLayerCoordinates()
                cellPos.x -= x
                cellPos.y -= y

                if layer.cellContainsBlockingInstance(cellPos):
                    return False

                cell = cellCache.getCell(cellPos)
                if cellCache.isCellInArea("water", cell):
                    return False

                # if not self.cellCache:
                #     self.cellCache = layer.getCellCache()
                # cell = self.cellCache.getCell(cellPos)
                # if cell.getCellType() != fife.CTYPE_NO_BLOCKER:
                #     return False

        # ## Check if the location is empty:
        # if not self.world.getInstacesInTile(location):
        self.instance.setLocation(location)
        return True


    def die(self):
        print "This unit is destroyed!"
        self.removeFootprint()
        #TODO: Enable attacking footprint area!
        self.world.unitDied(self.instance.getFifeId())
        # self.layer.deleteInstance(self.agent)


    def createFootprint(self):
        '''
        Creates a series of dummy objects to symbolize the free cells.
        :return:
        '''
        location = self.instance.getLocation()
        layer = location.getLayer()
        newlocation = self.instance.getLocation()
        dummyID = "dummy_%d" % self.getFifeId()
        for y in range(self.properties["SizeX"]):
            for x in range(self.properties["SizeY"]):
                cellPos = location.getLayerCoordinates()
                cellPos.x -= x
                cellPos.y -= y

                newlocation.setLayerCoordinates(cellPos)
                #dummyInstance = DummyInstance(self, newlocation)
                object = self.world.model.getObject("dummy", "fallen")
                #object = DummyInstance.getDummyObject()
                dummyInstance = layer.createInstance(object, newlocation.getExactLayerCoordinates())
                dummyInstance.setId(dummyID)

                visual = fife.InstanceVisual.create(dummyInstance)
                visual.setVisible(False)
                #dummyInstance.setVisual(visual)
                #if layer.addInstance(dummyInstance, newlocation.getExactLayerCoordinates()  ):
                #    print "Instance added!"

                self.dummyInstances.append(dummyInstance)
        self.landed = True


    def setFootprint(self):
        '''
        Sets the cells under this instance as blocking.
        :return:
        '''

        location = self.instance.getLocation()
        layer = location.getLayer()
        cellCache = layer.getCellCache()
        # anchorPos = location.getLayerCoordinates()

        for y in range(self.properties["SizeX"]):
            for x in range(self.properties["SizeY"]):
                cellPos = location.getLayerCoordinates()
                cellPos.x -= x
                cellPos.y -= y

                cell = cellCache.getCell(cellPos)
                cell.setCellType(fife.CTYPE_STATIC_BLOCKER)

        self.landed = True


    def removeFootprint(self):
        '''
        Sets the cells under this instance as blocking.
        :return:
        '''

        location = self.instance.getLocation()
        layer = location.getLayer()

        while len(self.dummyInstances) != 0:
            dummy = self.dummyInstances.pop()
            layer.deleteInstance(dummy)

        self.landed = False


    def start(self):
        self.createFootprint()
        if self.properties["StorageSize"] != 0:
                self.storage = Storage(self, self.world)


    def run(self):
        pass


    def _takeoff(self):
        '''
        Handles the launch of this Dropship to another planet..
        :return:
        '''

        possiblePlanets = list(self.world.faction.pwnedPlanets)
        for planet in self.world.faction.pwnedPlanets:
            possiblePlanets += self.world.universe.galaxy.planetLinks[planet]
        possiblePlanets = list(set(possiblePlanets)) # Remove duplicates
        selectPlanet = SelectPlanet(self.world.universe, selectablePlanets=possiblePlanets)
        targetPlanet = selectPlanet.execute()
        if not targetPlanet:
            return
        # Construct a dictionary with the contents of the storage.
        storageDict = self.storage.getStorageDict()
        ## Add the information to the "Attacking" dictionary.
        dropshipDict = {"storage" : storageDict,
                        "origin" : self.world.planet.name,
                        "target" : targetPlanet}
        self.world.universe.progress.attacking.append(dropshipDict)
        self.world.selectUnit(None)

        self.die()


    def _buildDropship(self):
        '''
        Starts the dropship building
        :return:
        '''
        if self.properties["faction"] == 'Human':
            buildingName = "Dropship"
        else:
            buildingName = "Saucer"

        self.world.startBuilding(buildingName, hideMenu=True)
        #
        # if self.world.construction:
        #     # get rid of the already loaded instance:
        #     self.world.stopBuilding()
        #
        # self.world.construction = self.scene.unitLoader.createBuilding(buildingName)
        #
        # self.world.setMode(self.world.MODE_DEPLOY)
