__author__ = 'cos'


from tactic_world import TacticWorld
from strategic_world import StrategicWorld
from fife.extensions import pychan




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


'''

class MainMenu(object):
    def __init__(self, world, setting):
        self._world = world
        self._setting = setting
        self._widget = pychan.loadXML('gui/mainmenu.xml')

        self._continue = self._widget.findChild(name="continue")
        self._newgame = self._widget.findChild(name="new_game")
        # self._credits = self._widget.findChild(name="credits")
        # self._highscores = self._widget.findChild(name="high_scores")
        self._quit = self._widget.findChild(name="quit")

        self._widget.position = (0, 0)

        eventMap = {
            'continue': self._world.continueGame,
            'new_game': self.hide,
            'settings': self._setting.showSettingsDialog,
            # 'credits': self._world.showCredits,
            # 'high_scores': self._world.showHighScores,
            'quit': self._world.quit,
        }

        self._widget.mapEvents(eventMap)

        self._continueMinWidth = self._continue.min_width
        self._continueMinHeight = self._continue.min_height
        self._continueMaxWidth = self._continue.max_width
        self._continueMaxHeight = self._continue.max_height


    def show(self, cont=False):
        if cont:
            self._continue.min_width = self._continueMinWidth
            self._continue.min_height = self._continueMinHeight
            self._continue.max_width = self._continueMaxWidth
            self._continue.max_height = self._continueMaxHeight

        else:
            self._continue.min_width = 0
            self._continue.min_height = 0
            self._continue.max_width = 0
            self._continue.max_height = 0

        self._continue.adaptLayout()
        self._widget.show()

    def hide(self):
        self._widget.hide()

    def isVisible(self):
        return self._widget.isVisible()

'''