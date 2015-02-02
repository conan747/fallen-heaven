__author__ = 'cos'


from tactic_world import TacticWorld
from strategic_world import StrategicWorld
from fife.extensions import pychan


class Faction(object):
    '''
    Holds the information about a faction i.e. a player and all its units and resources.
    '''
    name = None
    ownedProvinces = []
    resources = None
    technology = None

    def __init__(self):
        pass

    def load(self, filenName):
        '''
        Loads the faction info from a pickle.
        '''
        pass


class Universe(object):
    '''
    This will hold the overall campaign information.
    It also takes care of the main GUI where the player can choose the planet and end turn.
    So far it just creates two buttons:
    Start Strategic turn: Generates a strategic_world instance. It's the overall "building" mode.
    Start Tactical turn: Generates a tactic_world instance. It's the combat mode.
    '''

    pause = True

    def __init__(self, engine, settings):

        self._engine = engine
        self._settings = settings
        self.world = None

        # '''
        # Build the main GUI
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

        self.faction = "Human" # FIXME
        # '''

        # self.startTactic(str(self._settings.get("rio", "MapFile")))
        # self.startStrategic(str(self._settings.get("rio", "MapFile")))

    def newGame(self):
        '''
        Restarts the game.
        :return:
        '''
        if self.world:
            self.world.__destroy__()

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
        self.startTactic(str(self._settings.get("rio", "MapFile")))

    def toPlanetClicked(self):
        print "Going to Planet!"
        self.gui.hide()
        self.startStrategic(str(self._settings.get("rio", "MapFile")))

    def endTurn(self):
        pass

    def startTactic(self, mapFile):
        '''
        Starts Tactic mode.
        #TODO: Add parameter to select map.
        :return:
        '''

        self.world = TacticWorld(self._engine, self._settings)

        self.world.load(mapFile)
        print "Loading map: ", mapFile

    def startStrategic(self, mapFile):
        self.world = StrategicWorld(self._engine, self._settings)
        self.world.load(mapFile)
        print "Loading map: ", mapFile


    def pump(self):
        if self.pause:
            return
        if self.world:
            self.world.pump()

    # def quit(self):
    #     self._applictaion.requestQuit()
