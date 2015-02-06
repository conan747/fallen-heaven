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

    planetNames = ["shrine2", "savefile"]
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
        self.gui.show()

        self.faction = Faction("Human") # FIXME
        prog = Progress(self)


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

        engine = self._engine
        settings = self._settings
        self.continueGame()

    def pauseGame(self):
        self.pause = True

    def continueGame(self):
        self.pause = False

    def toWarClicked(self):
        print "Going to war!"
        self.gui.hide()
        self.selectedPlanet = Planet("firstCapital")
        self.startTactic()

    def toPlanetClicked(self):
        print "Going to Planet!"
        self.gui.hide()
        self.selectedPlanet = Planet("firstCapital")
        self.startStrategic()

    def endTurn(self):
        pass

    def startTactic(self):
        '''
        Starts Tactic mode.
        :return:
        '''

        self.world = TacticWorld(self._engine, self._settings, self.faction, self.selectedPlanet)

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
