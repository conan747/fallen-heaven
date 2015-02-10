__author__ = 'cos'



from fife import fife
from agents.cloud import Cloud
from agents.unit import *
from agents.building import *
from fife.extensions.fife_settings import Setting

from gui.huds import TacticalHUD
from combat import Trajectory

from fife.extensions.savers import saveMapFile
import cPickle as pickle


# Temp:
import os


_MODE_DEFAULT, _MODE_ATTACK, _MODE_DROPSHIP = xrange(3)




class UnitLoader(object):
    '''
    Reads the unit text files and generates unit property objects.
    It can be used to obtain unit and building objects (without attached instances).
    '''


    def __init__(self, world, settings):

        self.unitProps = {}
        self.weaponProps = {}
        self.buildingProps = {}

        self.world = world
        self.settings = settings

        self.parseUnitFile ("objects/agents/alien.units", "Tauran")
        self.parseWeaponFile("objects/agents/alien.weapons", "Tauran")
        self.parseBuildingFile("objects/agents/alien.buildings", "Tauran")
        self.parseUnitFile("objects/agents/human.units", "Human")
        self.parseWeaponFile("objects/agents/human.weapons", "Human")
        self.parseBuildingFile("objects/agents/human.buildings", "Human")


    def parseFile(self, filename):
        returnDict = {}
        fil = open(filename)
        wholeText = fil.readlines()
        fil.close()
        # remove the lines starting with ";" and "\n"
        wholeText = [text for text in wholeText if text[0] != ";" if text != "\n"]

        # Get indexes of the beginning of units (marked by "[]".
        IDCells = [text for text in wholeText if text[0] == "["]

        for IDCell in IDCells:
            ID = IDCell.split("]")[0].split("[")[1]
            propertyObj = {}

            propertyText = []
            for i in range(wholeText.index(IDCell)+1, wholeText.__len__()):
                if wholeText[i][0] == "[":
                    break # We parsed all the object and found the next object.

                propertyText.append(wholeText[i])

            # Now we have to parse this propertyText.
            for line in propertyText:
                if not "=" in line:
                    continue
                name, value = line.split("=")
                value = value.split("\n")[0]
                numvalue = None

                try:
                    numvalue = int(value) + 0
                except:
                    numvalue = value

                propertyObj[name] = numvalue

            returnDict[ID] = propertyObj

        return returnDict


    def parseUnitFile(self, filename, faction):
        unitDict = self.parseFile(filename)
        for unit in unitDict.keys():
            unitDict[unit]["unitName"] = unit
            unitDict[unit]["faction"] = faction
            unitDict[unit]["type"] = "Unit"
        self.unitProps.update(unitDict)


    def parseWeaponFile(self, filename, faction):
        weaponDict = self.parseFile(filename)
        for weapon in weaponDict.keys():
            weaponDict[weapon]["weaponName"] = weapon
            weaponDict[weapon]["faction"] = faction
            weaponDict[weapon]["type"] = "Weapon"
        self.weaponProps.update(weaponDict)


    def parseBuildingFile(self, filename, faction):
        buildingDict = self.parseFile(filename)
        for building in buildingDict.keys():
            buildingDict[building]["buildingName"] = building
            buildingDict[building]["faction"] = faction
            buildingDict[building]["type"] = "Building"
        self.buildingProps.update(buildingDict)


    def createBuilding(self, buildingName):

        if buildingName not in self.buildingProps.keys():
            return "Found no building with that buildingName!"
        buildingProps = self.buildingProps[buildingName]
        buildingProps["unitName"] = buildingName
        newBuilding = Building(self.world, buildingProps)
        # newBuilding.properties = buildingProps
        return newBuilding


    def createUnit(self, unitName):
        if unitName not in self.unitProps.keys():
            return "Found no unit with that unitName!"

        unitProps = self.unitProps[unitName]
        lWeapon = Weapon(self.world)
        weaponName = unitProps["LightWeapon"]
        lWeapon.properties = self.weaponProps[weaponName]
        hWeapon = Weapon(self.world)
        weaponName = unitProps["HeavyWeapon"]
        hWeapon.properties = self.weaponProps[weaponName]

        newUnit = Unit(self.world, unitProps)
        newUnit.lightWeapon = lWeapon
        newUnit.heavyWeapon = hWeapon

        return newUnit


    def isUnit(self, id):
        if id in self.unitProps.keys():
            return True
        else:
            return False

    def isBuilding(self, id):
        if id in self.buildingProps.keys():
            return True
        else:
            return False



class Scene(object):
    """
    Master game scene.  Keeps track of all game objects.

    This is the meat and potatoes of the game.  This class takes care of all the units.
    """

    def __init__(self, world, engine):
        """
        @param world: A reference to the master instance of the World class
        @type world: L{World}
        @param engine: A reference to the FIFE engine
        @type engine: L{fife.Engine}
        @param objectLayer: The layer that all objects exist on
        @type objectLayer: L{fife.Layer}
        """
        self.engine = engine
        self._world = world
        self._model = engine.getModel()
        self.agentLayer = None

        self._music = None
        self.instance_to_agent = {}
        self.factionUnits = {}
        self._player1 = True
        self._player2 = False
        self.faction = self._world.faction
        self.planet = self._world.planet

        self.unitLoader = UnitLoader(self._world, self._world.settings)

    def destroy(self):
        """
        Removes all objects from the scene and deletes them from the layer.
        """
        for agent in self.instance_to_agent.values():
            if hasattr(agent, "storage"):
                del agent.storage
            del agent

    def getInstacesInTile(self, tileLocation):
        '''
        Returns a list of instance IDs that are located in the specific tile.
        :param tileLocation: Exact Location of a tile.
        :return: List of instance IDs.
        '''

        tilePos = tileLocation.getLayerCoordinates()
        unitIDs = []
        all_instances = self.agentLayer.getInstances()
        for instance in all_instances:
            instanceLocation = instance.getLocation().getLayerCoordinates()
            if tilePos == instanceLocation:
                unitIDs.append(instance.getFifeId())

        print "Found ", unitIDs.__len__(), " units on this tile."
        print unitIDs

        return unitIDs


    def getInstance(self, id):
        # TODO See if we can get rid of this by replacing it with instance_to_agent .agent
        '''
        :param id: FIFEID of the agent you want to obtain
        :return: Instance
        '''
        ids = self.agentLayer.getInstances()
        instance = [i for i in ids if i.getFifeId() == id]
        if instance:
            return instance[0]

    def pump(self):
        pass


    def load(self, filename):
        """
        Load a xml map and setup agents and cameras.
        """
        self.filename = filename
        loader = fife.MapLoader(self.engine.getModel(),
                                self.engine.getVFS(),
                                self.engine.getImageManager(),
                                self.engine.getRenderBackend())

        if not loader.isLoadable(filename):
            print "Problem loading map: map file is not loadable"
            return

        self.map = loader.load(filename)

        self._world.initCameras()
        self.initAgents()
        # self.initCameras()

        #Set background color
        self.engine.getRenderBackend().setBackgroundColor(0,0,0)


        ## Load storages:
        storageFile = filename.replace(".xml",".sto")
        if os.path.isfile(storageFile):
            pic = pickle.load(open(storageFile, 'rb'))
            for building in self.instance_to_agent.values():
                if building.agentName in pic.keys():
                    info = pic[building.agentName]
                    print "Setting up", info
                    building.storage.setStorage(info)


    def initAgents(self):
        """
        Setup agents.

        Loads the "agents" (i.e. units and structures) from the planet object and initialises them.
        """

        self.agentLayer = self.map.getLayer('TechdemoMapGroundObjectLayer')
        if not self.agentLayer:
            print "Using the first layer that was found: ", self.map.getLayers()[0].getId()
            self.agentLayer = self.map.getLayers()[0]

        agentList = self.planet.agentInfo
        self.planet.agentInfo = {}

        for agentID in agentList.keys():
            id = agentID
            agentType = id.split(":")[0] # Holds the unit or stucture name

            if self.unitLoader.isUnit(agentType):
                newUnit = self.unitLoader.createUnit(agentType)
                newUnit.AP = agentList[agentID]["AP"]
            elif self.unitLoader.isBuilding(agentType):
                newUnit = self.unitLoader.createBuilding(agentType)
            else:
                print "Error: unit is not building nor unit! ??"
                continue

            location = agentList[agentID]["Location"]
            newUnit.createInstance(location)
            self.instance_to_agent[newUnit.agent.getFifeId()] = newUnit
            newUnit.start()

            # Apply storage:
            if agentID in self.planet.storages.keys():
                storage = self.planet.storages[agentID]
                newUnit.storage.setStorage(storage)
                self.planet.storages[agentID] = None



            # Apply health:
            newUnit.health = agentList[agentID]["HP"]

            print id , "loaded!"

                    # if newUnit.nameSpace == "Building":
                    #     newUnit.setFootprint()

    def updatePlanetAgents(self):
        '''
        Updates the agent information (units and structures) that the planet object stores.
        :return:
        '''
        self.planet.agentInfo = {}
        for angent in self.instance_to_agent.values():
            self.planet.saveInstance(angent)



    def getStorageDicts(self):
        '''
        Return a dictionary containing the storages of the buildings in this scene.
        :return:
        '''
        storages = {}

        for agentName in self.instance_to_agent.keys():
            agent = self.instance_to_agent[agentName]
            if agent.agentType == "Building":
                if agent.storage:
                    # Add this to the storages
                    if agent.storage.inProduction or agent.storage.unitsReady:
                        thisStorage = {"inProduction" : agent.storage.inProduction,
                                       "unitsReady" : agent.storage.unitsReady}
                        storages[agent.agentName] = thisStorage

        print "Saving" , len(storages), "storages"

        return storages
