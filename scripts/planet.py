__author__ = 'cos'

from scene import Scene
import cPickle as pickle




class Planet(object):
    '''
    Stores the information to load a map.
    '''

    name = None # Name of the planet. Used to figure out map file.
    storages = {} # Dictionary containing the information for building storages.
    agentInfo = {} # Information of each Agent on the map.
    _fileNameTemplate = "maps/planet.plt"

    def __init__(self, planetName=""):
        self.name = planetName
        self.load()


    def getMapPath(self):
        return "maps/" + self.name + ".xml"

    def saveInstance(self, agent):
        '''
        Saves the temporal information of this agent.
        :param agent:
        :return:
        '''
        agentName = agent.agentName
        info = {}
        info["HP"] = agent.health
        if agent.nameSpace == "Unit":
            info["AP"] = agent.AP

        self.agentInfo[agentName] = info

    def save(self):
        '''
        Pickles the planet. (Try saying it three times)
        :return:
        '''
        tosave = { "name" : self.name,
                   "agentInfo" : self.agentInfo,
                   "storages" : self.storages}
        fileName = self._fileNameTemplate.replace("planet", self.name)
        pickle.dump(tosave, open(fileName, 'wb'))

    def load(self):
        '''
        Load previously saved planet information.
        :return:
        '''
        fileName = self._fileNameTemplate.replace("planet", self.name)
        pickleFile = open(fileName, 'rb')
        if not pickleFile:
            return False
        content = pickle.load(pickleFile)
        pickleFile.close()

        for attr in content.keys():
            setattr(self, attr, content[attr])