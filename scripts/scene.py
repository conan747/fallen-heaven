__author__ = 'cos'



from fife import fife
from agents.cloud import Cloud
from agents.unit import *
from agents.building import *
from fife.extensions.fife_settings import Setting

from gui.huds import TacticalHUD
from combat import Trajectory

from fife.extensions.savers import saveMapFile



_MODE_DEFAULT, _MODE_ATTACK, _MODE_DROPSHIP = xrange(3)




class UnitLoader(object):
    '''
    Reads the unit text files and generates unit property objects.
    '''



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
        self.unitProps.update(unitDict)


    def parseWeaponFile(self, filename, faction):
        weaponDict = self.parseFile(filename)
        for weapon in weaponDict.keys():
            weaponDict[weapon]["weaponName"] = weapon
            weaponDict[weapon]["faction"] = faction
        self.weaponProps.update(weaponDict)


    def parseBuildingFile(self, filename, faction):
        buildingDict = self.parseFile(filename)
        for building in buildingDict.keys():
            buildingDict[building]["buildingName"] = building
            buildingDict[building]["faction"] = faction
        self.buildingProps.update(buildingDict)


    def createBuilding(self, buildingName):

        if buildingName not in self.buildingProps.keys():
            return "Found no building with that buildingName!"
        buildingProps = self.buildingProps[buildingName]
        newBuilding = Building(buildingName, self.world)
        newBuilding.properties = buildingProps
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



class Scene(object):
    """
    Master game scene.  Keeps track of all game objects.

    This is the meat and potatoes of the game.  This class takes care of the scene graph,
    updating objects, destroying objects, collision detection, etc etc.
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

        self.unitLoader = UnitLoader(self._world, self._world.settings)

    def destroyScene(self):
        """
        Removes all objects from the scene and deletes them from the layer.
        """
        pass

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

        # Temp
        for id in unitIDs:
            unit = self.instance_to_agent[id]
            unit.printProperties()

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

    def reset(self):
        pass

    def initScene(self, mapobj):
        """
		Initializess the scene and scene graph.  This creates game objects for
		FIFE instances that exist in the map.

		"""
        self.map, self.agentLayer = None, None
        self.cameras = {}
        self.cur_cam2_x, self.initial_cam2_x, self.cam2_scrolling_right = 0, 0, True
        self.target_rotation = 0
        self.instance_to_agent = {}


    def load(self, filename):
        """
        Load a xml map and setup agents and cameras.
        """
        self.filename = filename
        self.reset()
        loader = fife.MapLoader(self.engine.getModel(),
                                self.engine.getVFS(),
                                self.engine.getImageManager(),
                                self.engine.getRenderBackend())

        if loader.isLoadable(filename):
            self.map = loader.load(filename)

        self._world.initCameras()
        self.initAgents()
        # self.initCameras()

        #Set background color
        self.engine.getRenderBackend().setBackgroundColor(80,80,255)

        ## Start cellRenderer to show instance paths:
        self.cellRenderer = fife.CellRenderer.getInstance(self._world.cameras['main'])
        self.cellRenderer.addActiveLayer(self.agentLayer)
        # self.cellRenderer.activateAllLayers(self.map)
        self.cellRenderer.setEnabledBlocking(True)
        self.cellRenderer.setEnabled(True)


    def initAgents(self):
        """
        Setup agents.

        For this techdemo we have a very simple 'active things on the map' model,
        which is called agents. All rio maps will have a separate layer for them.

        Note that we keep a mapping from map instances (C++ model of stuff on the map)
        to the python agents for later reference.
        """

        self.agentLayer = self.map.getLayer('TechdemoMapGroundObjectLayer')

        id_to_class = {"PC": "Squad",
                    "NPC" : "Squad",
                    "beach_bar": "Barrack"}

        allInstances = self.agentLayer.getInstances()

        for instance in allInstances:
            id = instance.getId()
            agentFound = id.split(":")[0]
            if agentFound in id_to_class.keys():
                agentName = id_to_class[agentFound]

                if self.unitLoader.isUnit(agentName):
                    newUnit = self.unitLoader.createUnit(agentName)
                elif self.unitLoader.isBuilding(agentName):
                    newUnit = self.unitLoader.createBuilding(agentName)
                else:
                    continue

                newUnit.selectInstance(id)
                self.instance_to_agent[newUnit.agent.getFifeId()] = newUnit
                newUnit.start()
                print id , "loaded!"

                # if isinstance(newUnit,Building):
                #     newUnit.setFootprint()
                if newUnit.nameSpace == "Building":
                    newUnit.setFootprint()

                ## FIXME: A fix to test the loading of units
                if id == "PC":
                    self.factionUnits[self._player1] = [newUnit.agent.getFifeId()]
                elif id == "NPC":
                    self.factionUnits[self._player2] = [newUnit.agent.getFifeId()]



    def save(self, filename):
        print "Saving map..."
        saveMapFile(filename, self.engine, self.map)
