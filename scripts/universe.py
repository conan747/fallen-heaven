__author__ = 'cos'


from tactic_world import TacticWorld
from strategic_world import StrategicWorld
from fife.extensions import pychan
from progress import Progress
from planet import Planet
from faction import Faction

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
        # TODO: Probably we would like to separate this into another GUI object.
        self.gui = pychan.loadXML('gui/universe_screen.xml')
        self.gui.min_size = self._engine.getRenderBackend().getScreenWidth(), self._engine.getRenderBackend().getScreenHeight()

        eventMap = {
            'toWar': self.toWarClicked,
            'toPlanet': self.toPlanetClicked,
            'endTurn': self.endTurn,
        }
        self.gui.mapEvents(eventMap)

        # Finally show the main GUI
        # self.gui.show()

        # self.faction = Faction("Human") # FIXME
        self.faction = None


    def load(self, name="Human"):
        saveDir = "saves/test/"
        self.progress = Progress(self)
        self.progress.load(saveDir + name + ".sav")
        self.gui.show()

        self.faction = Faction()
        self.faction.__setInfo__(self.progress.factions[self.progress.playerFactionName])
        # self.planetNames = self.progress.allPlanets.keys()
        self.continueGame()


    def newGame(self):
        '''
        Restarts the game.
        :return:
        '''
        #FIXME: Look into restarting the program.
        if self.world:
            self.world.model.deleteMaps()
            self.world.model.deleteObjects()
            self.world = None

        self.gui.show()

        self.progress = Progress(self) # to save the progress.
        self.faction = Faction("Human")
        faction2 = Faction("Tauran")
        self.progress.factions["Human"] = self.faction
        self.progress.factions["Tauran"] = faction2

        planetNames = ["firstCapital", "secondPlanet"]
        for planetName in planetNames:
            planet = Planet(planetName)
            self.progress.allPlanets[planetName] = planet.getPlanetDict()

        self.continueGame()

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

    def toPlanetClicked(self):
        print "Going to Planet!"
        self.gui.hide()
        planetName = "firstCapital"
        planetInfo = self.progress.allPlanets[planetName]
        self.selectedPlanet = Planet(planetName, planetInfo)
        self.startStrategic()

    def endTurn(self):
        pass

    def startTactic(self):
        '''
        Starts Tactic mode.
        :return:
        '''

        self.world = TacticWorld(self._engine, self._settings, self.faction, self.selectedPlanet, self.progress.factions)

        self.world.load(self.selectedPlanet.getMapPath())
        print "Loading map: ", self.selectedPlanet.getMapPath()

    def startStrategic(self):
        self.world = StrategicWorld(self._engine, self._settings, self.faction, self.selectedPlanet)
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
        if self.world.scene:
            self.world.scene.updatePlanet()
        self.progress.save()