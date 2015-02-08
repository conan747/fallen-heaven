__author__ = 'cos'

from scene import Scene
import cPickle as pickle
import os




class Planet(object):
    '''
    Stores the information to load a map.
    '''

    name = None # Name of the planet. Used to figure out map file.
    storages = {} # Dictionary containing the information for building storages.
    agentInfo = {} # Information of each Agent on the map.
    _fileNameTemplate = "saves/test/planet.plt"

    def __init__(self, planetName="", planetInfo = None):
        self.name = planetName
        self.load(planetInfo)


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

        # Location
        location = agent.agent.getLocation()
        point = location.getLayerCoordinates()
        info["Location"] = (point.x , point.y, point.z)

        if agent.agentType == "Unit":
            info["AP"] = agent.AP

        self.agentInfo[agentName] = info


    def getPlanetDict(self):
        tosave = { "name" : self.name,
                   "agentInfo" : self.agentInfo,
                   "storages" : self.storages}
        return tosave

    def save(self):
        '''
        Pickles the planet. (Try saying it three times)
        :return:
        '''
        tosave = self.getPlanetDict()
        fileName = self._fileNameTemplate.replace("planet", self.name)
        pickle.dump(tosave, open(fileName, 'wb'))

    def load(self, planetInfo = None):
        '''
        Load previously saved planet information, or imports planetInfo into this planet.
        :return:
        '''
        if not planetInfo:
            fileName = self._fileNameTemplate.replace("planet", self.name)
            if os.path.isfile(fileName):
                pickleFile = open(fileName, 'rb')
            else:
                return False
            content = pickle.load(pickleFile)
            pickleFile.close()

        else:
            content = planetInfo
            assert content["name"] == self.name, "trying to copy info from planet %r into planet %r" % (content["name"], self.name)


        for attr in content.keys():
            setattr(self, attr, content[attr])