__author__ = 'cos'


from tactic_world import TacticWorld
from strategic_world import StrategicWorld
from fife.extensions import pychan
from progress import Progress
from planet import Planet


class Faction(object):
    '''
    Holds the information about a faction i.e. a player and all its units and resources.
    '''
    name = None
    pwnedPlanets = []
    resources = None
    technology = None

    # _RES_ENERGY, _RES_CREDITS, _RES_RESEARCH = xrange(3)

    def __init__(self, name= ""):
        resources = {"Energy": 0,
                     "Credits" : 0,
                     "Research" : 0}

        technology = {"Energy" : 1,
                      "Armor" : 1,
                      "Movement" : 1,
                      "Damage" : 1,
                      "RateOfFire" : 1,
                      "Rocketry" : 1}

        self.name = name

        self.pwnedPlanets.append("shrine2")



class Universe(object):
    '''
    This will hold the overall campaign information.
    It also takes care of the main GUI where the player can choose the planet and end turn.
    So far it just creates two buttons:
    Start Strategic turn: Generates a strategic_world instance. It's the overall "building" mode.
    Start Tactical turn: Generates a tactic_world instance. It's the combat mode.
    '''

    planets = ["shrine2", "savefile"]
    selectedPlanet = None

    pause = True

    def __init__(self, engine, settings):

        self._engine = engine
        self._settings = settings
        self.world = None
        self.turn = 1

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

        self.faction = Faction("Human") # FIXME
        prog = Progress(self)
        # print dir(self.faction)
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
        self.selectedPlanet = Planet("shrine2")
        self.startTactic()

    def toPlanetClicked(self):
        print "Going to Planet!"
        self.gui.hide()
        self.selectedPlanet = Planet("shrine2")
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
