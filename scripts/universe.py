__author__ = 'cos'


from tactic_world import TacticWorld
from strategic_world import StrategicWorld
from fife.extensions import pychan




class Universe(object):
    '''
    This will hold the overall campaign information
    '''

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
        if self.world:
            self.world.pump()