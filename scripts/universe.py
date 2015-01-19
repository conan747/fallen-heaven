__author__ = 'cos'


from world import World




class Universe(object):
    '''
    This will hold the overall campaign information
    '''

    def __init__(self, engine, settings):

        self._engine = engine
        self._settings = settings
        self.world = None

        self.startTactic(str(self._settings.get("rio", "MapFile")))


    def startTactic(self, mapFile):
        '''
        Starts Tactic mode.
        #TODO: Add parameter to select map.
        :return:
        '''

        self.world = World(self._engine, self._settings)

        self.world.load(mapFile)
        print "Loading map: ", mapFile

    def pump(self):
        if self.world:
            self.world.pump()