__author__ = 'cos'


from tactic_world import TacticWorld
from strategic_world import StrategicWorld
from progress import Progress
from planet import Planet
from faction import Faction
from gui.universeUI import UniverseUI
from campaign import Campaign

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

        # '''
        # Build the main GUI
        self.gui = UniverseUI(self)
        self.gui.mapEvents = {
            "endTurn" : self.endTurn
        }

        self.faction = None



    def load(self):
        saveDir = "saves/test/"
        self.progress = Progress(self)
        self.campaign = Campaign(self, "saves/test/ForeverWar.cpn")
        self.progress = self.campaign.progress

        # self.progress.load(saveDir + name + ".sav")
        self.gui.show()

        self.faction = Faction()
        self.faction.__setInfo__(self.progress.factionInfo)
        # self.planetNames = self.progress.allPlanets.keys()
        self.continueGame()
        self.gui.updateUI()


    def newGame(self):
        '''
        Creates a new campaign and starts it.
        :return:
        '''
        #FIXME: Look into restarting the program.
        if self.world:
            self.world.model.deleteMaps()
            self.world.model.deleteObjects()
            self.world = None

        self.gui.show()

        self.campaign = Campaign(self)
        self.campaign.newCampaign()

        self.progress = self.campaign.progress # to save the progress.
        self.faction = Faction()
        self.faction.__setInfo__(self.progress.factionInfo)
        # self.faction = Faction("Human")
        # faction2 = Faction("Tauran")
        # self.progress.factions["Human"] = self.faction
        # self.progress.factions["Tauran"] = faction2

        planetNames =  self.campaign.planetList#["firstCapital", "secondPlanet"]
        for planetName in planetNames:
            planet = Planet(planetName)
            self.progress.allPlanets[planetName] = planet.getPlanetDict()

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
        self.progress.allPlanets[planetName]
        self.selectedPlanet = Planet(planetName, self.progress.allPlanets[planetName])
        self.startTactic()

    def toCapitalClicked(self):
        print "Going to Planet!"
        self.gui.hide()
        planetName = "firstCapital"
        planetInfo = self.progress.allPlanets[planetName]
        self.selectedPlanet = Planet(planetName, planetInfo)
        self.startStrategic()

    def toPlanetClicked(self):
        print "Going to Planet!"
        self.gui.hide()
        planetName = "secondPlanet"
        planetInfo = self.progress.allPlanets[planetName]
        self.selectedPlanet = Planet(planetName, planetInfo)
        self.startStrategic()

    def goToPlanet(self, planetName):
        print "Going to Planet ", planetName
        self.gui.hide()
        if planetName in self.progress.allPlanets.keys():
            planetInfo = self.progress.allPlanets[planetName]
        else:
            planetInfo = None
        self.selectedPlanet = Planet(planetName, planetInfo)
        self.startStrategic()

    def endTurn(self):
        pass

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

    # def quit(self):
    #     self._applictaion.requestQuit()

    def save(self):
        if self.world:
            if self.world.scene:
                # self.world.scene.save("test.xml")
                self.world.scene.updatePlanetAgents()
        self.campaign.saveCampaign()
        # self.progress.save()

    def backToUniverse(self):
        # Save the information
        self.progress.update()

        self.world.scene.destroy()
        self.world.HUD.closeExtraWindows()

        # delete map and objects.
        model = self._engine.getModel()
        model.deleteMaps()
        model.deleteObjects()

        self.world.listener.detach()
        del self.world.listener
        self.world.music.stop()
        del self.world.music
        self.world.waves.stop()
        del self.world.waves
        # self.world.soundmanager.releaseEmitter(id)
        del self.world.soundmanager
        # del self.world.waves
        self.world.scene = None
        self.world.HUD.destroy()
        self.world.HUD = None

        self.world.scene = None
        self.world = None

        if self.selectedPlanet:
            self.selectedPlanet = None

        self.gui.show()


    def endTurn(self):
        '''
        Ends the current turn. This implies:
        - Saves the information for this turn and should send it.
        - Leaves the game at a state where it's waiting the input from the other player.
        - After the other pla
        :return:
        '''

        self.progress.faction = self.faction
        self.progress.save()
        self.campaign.compileYear()