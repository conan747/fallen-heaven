__author__ = 'cos'


from tactic_world import TacticWorld
from strategic_world import StrategicWorld
from galaxy import *
from faction import Faction
from gui.universeUI import UniverseUI
from campaign import Campaign

from agents.unit import *
from agents.building import *

import Tkinter, tkFileDialog

from engine.sound import Sound


class UnitLoader(object):
    '''
    Reads the unit text files and generates unit property objects.
    It can be used to obtain unit and building objects (without attached instances).
    '''

    def __init__(self, settings, world=None):

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

    def setWorld(self, world):
        self.world = world

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

        if not self.world:
            print "Error: No world associated with UnitCreator!"
            return

        if buildingName not in self.buildingProps.keys():
            print "Found no building with that buildingName!"
            return
        buildingProps = self.buildingProps[buildingName]
        buildingProps["unitName"] = buildingName

        newBuilding = Building(self.world, buildingProps)
        # newBuilding.properties = buildingProps
        return newBuilding


    def createUnit(self, unitName):

        if not self.world:
            print "Error: No world associated with UnitCreator!"
            return

        if unitName not in self.unitProps.keys():
            return "Found no unit with that unitName!"

        unitProps = self.unitProps[unitName]
        lWeapon = Weapon(self.world)
        weaponName = unitProps["LightWeapon"]
        lWeapon.properties = self.weaponProps[weaponName]
        hWeapon = Weapon(self.world)
        weaponName = unitProps["HeavyWeapon"]
        hWeapon.properties = self.weaponProps[weaponName]

        newUnit = Unit(self.world, unitProps, lWeapon=lWeapon, HWeapon=hWeapon)

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





class Universe(object):
    '''
    This will hold the overall campaign information.
    It also takes care of the main GUI where the player can choose the planet and end turn.
    So far it just creates two buttons:
    Start Strategic turn: Generates a strategic_world instance. It's the overall "building" mode.
    Start Tactical turn: Generates a tactic_world instance. It's the combat mode.
    '''


    selectedPlanet = None

    pause = True

    def __init__(self, engine, settings):

        self._engine = engine
        self._settings = settings
        self.world = None
        self.year = 1   # Equivalent to "turn" in strategic view.
        self.gui = None

        self.campaign = None
        self.progress = None
        self.galaxy = None

        self.faction = None

        self.sound = Sound(self._engine, self._settings)

        self.unitLoader = UnitLoader(self._settings)



    def load(self):


        saveDir = "saves/test/"
        # self.progress = Progress(self)
        root = Tkinter.Tk()
        file = tkFileDialog.askopenfilename(parent=root,
                                        title='Select campaign to load',
                                        initialdir=saveDir,
                                        filetypes=[("Campaign", "*.cpn")])

        self.campaign = Campaign(self, file)
        root.destroy()
        self.newGame()



    def newGame(self, campaign=None, giveFreebies=False):
        '''
        Creates a new campaign and starts it.
        :return:
        '''
        #FIXME: Look into restarting the program.
        if self.world:
            self.world.model.deleteMaps()
            self.world.model.deleteObjects()
            self.unitLoader.setWorld(None)

        if campaign:
            self.campaign = campaign
        elif not self.campaign:
            self.campaign = Campaign(self)
            self.campaign.createCampaign()

        self.galaxy = Galaxy(self.campaign.galaxyName)

        # Build the main GUI
        if not self.gui:
            self.gui = UniverseUI(self)

        self.gui.show()

        self.progress = self.campaign.progress # to save the progress.
        self.faction = Faction()
        self.faction.__setInfo__(self.progress.factionInfo)

        # Give a freebie of 10000 credits
        if giveFreebies:
            self.faction.resources["Credits"] = 10000


        self.continueGame()
        self.gui.updateUI()

    def pauseGame(self):
        self.pause = True

    def continueGame(self):
        self.pause = False

    def toWarClicked(self):
        print "Going to war!"
        self.gui.hide()
        planetName = "firstCapital"
        #self.progress.allPlanets[planetName]
        self.selectedPlanet = Planet(planetName, self.progress.allPlanets[planetName])
        self.startTactic()

    def goToPlanet(self, planetName):
        print "Going to Planet ", planetName
        self.gui.hide()
        if planetName in self.progress.allPlanets.keys():
            planetInfo = self.progress.allPlanets[planetName]
        else:
            planetInfo = None
        self.selectedPlanet = Planet(planetName, planetInfo)
        self.startStrategic()

    def startTactic(self):
        '''
        Starts Tactic mode. Loads TacticWorld.
        :return:
        '''

        self.world = TacticWorld(self, self.selectedPlanet)
        self.world.load(self.selectedPlanet.getMapPath())
        print "Loading map: ", self.selectedPlanet.getMapPath()

    def startStrategic(self):
        '''
        Starts strategic mode. Loads StrategicWorld.
        :return:
        '''
        self.world = StrategicWorld(self, self.selectedPlanet)
        self.world.load(self.selectedPlanet.getMapPath())
        print "Loading map: ", self.selectedPlanet.getMapPath()


    def pump(self):
        if self.pause:
            return
        if self.world:
            self.world.pump()


    def save(self):
        if self.world:
            self.world.updatePlanetAgents()
        self.campaign.saveCampaign()
        # self.progress.save()


    def backToUniverse(self):
        # Save the information
        self.progress.update()

        self.world.HUD.closeExtraWindows()
        self.world.destroy()
        self.world.view.end()

        self.world.listener.detach()
        # if self.world.music:
        #     self.world.music.stop()
        #     del self.world.music
        self.world.HUD.destroy()
        self.world.HUD = None

        self.unitLoader.setWorld(None)

        if self.selectedPlanet:
            self.selectedPlanet = None

        # delete map and objects.
        model = self._engine.getModel()
        model.deleteObjects()

        self.world = None
        self.gui.show()


    def getPlanetResources(self, planetName, display=False):
        '''
        Calculates the resources of a given planet.
        :param planetName: name of the planet to calculate
        :return: a tuple containing: (cash, energy, research)
        '''


        cashConsumption = 0
        cashProduction = 0
        energyConsumption = 0
        energyProduction = 0
        researchProduction = 0

        planet = self.progress.allPlanets[planetName]
        for agentID in planet["agentInfo"]:
            agentName = agentID.split(":")[0]
            if self.unitLoader.isBuilding(agentName):
                buildingProps = self.unitLoader.buildingProps[agentName]
                cashProduction += buildingProps["ProductionCash"]
                energyConsumption += buildingProps["ConsummationEnergy"]
                energyProduction += buildingProps["ProductionEnergy"]
                researchProduction += buildingProps["ProductionResearch"]

            elif self.unitLoader.isUnit(agentName):
                unitProps = self.unitLoader.unitProps[agentName]
                cashConsumption += unitProps["Upkeep"]
            else:
                print "Error, no agent type found for ", agentName

        for storage in planet["storages"].values():
            ## Should we also add the "inProduction" to the upkeep costs? So far no.
            for unitID in storage["unitsReady"]:
                agentName = unitID.split(":")[1]
                unitProps = self.unitLoader.unitProps[agentName]
                cashConsumption += unitProps["Upkeep"]

        totalCash = cashProduction - cashConsumption
        totalEnergy = energyProduction - energyConsumption

        if display:
            print "\nPlanet resource summary:"
            print "Planet name: ", planetName
            print "Cash flow: %d - %d = %d" % (cashProduction, cashConsumption, totalCash)
            print "Energy flow: %d - %d = %d" % (energyProduction, energyConsumption, totalEnergy)

        return (totalCash, totalEnergy, researchProduction)


    def updateResources(self):
        '''
        Calculates the resources and updates the faction information.
        :return:
        '''

        cashDelta = 0
        researchDelta = 0

        for planet in self.faction.pwnedPlanets:
            (cash, energy, research) = self.getPlanetResources(planet, display=True)
            cashDelta += cash
            researchDelta += research

        print "Total cash this turn:", cashDelta
        print "Research points this turn:", researchDelta
        self.faction.resources["Credits"] += cashDelta
        self.faction.resources["Research"] += researchDelta



    def endTurn(self):
        '''
        Ends the current turn. This implies:
        - Saves the information for this turn and should send it.
        - Leaves the game at a state where it's waiting the input from the other player.
        :return:
        '''

        print "Skipping turn!"

        self.updateResources()
        self.progress.faction = self.faction
        self.progress.save()
        self.campaign.compileYear()
        self.campaign.paused = True
        self.campaign.saveCampaign()

        self.gui.updateUI()
        # dialog = InfoDialog(message="Send the automatically generated .yer file and wait for the response.",
        #                     title= "Turn skipped.")
        # dialog.show()