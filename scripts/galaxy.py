__author__ = 'cos'

import cPickle as pickle
import os


class Galaxy(object):
    '''
    Holds the information of the different planets available and their display.
    '''

    _dir = "maps/"
    _extension = ".gal"

    def __init__(self, name="default"):
        self.name = name
        self.planetList = []
        self.planetLinks = {} # Gives the planets that are reachable from the "key" planet.
        self.image = "" # Path to the background image for the universe window.
        self.planteLocation = {} # Contains the coordinates of the planet to display.
        self.planetIm = {} # Contains the path to the images that represent the planet.
        self.planetList = self.getPlanetNames()





    def load(self, name=None):
        if name:
            self.name = name

        if not os.path.exists(self._dir + self.name + self._extension):
            print "Error loading galaxy: ", self.name
            return

        self.planetList = self.getPlanetNames()


    def getPlanetNames(self):
        '''
        Gets a list of planet names from the map directory
        :return:
        '''
        if self.planetList:
            return self.planetList

        # TODO: Contemplate loading planets depending on galaxy.
        fileNames = os.listdir("maps")
        planetNames = [fileName.split(".xml")[0] for fileName in fileNames
                       if ".xml" in fileName]
        print "Found planets: "
        print planetNames
        return planetNames



class Planet(object):
    '''
    Stores the information to load a map.
    '''


    _fileNameTemplate = "saves/test/planet.plt"

    def __init__(self, planetName="", planetInfo = None):
        self.name = planetName
        self.storages = {} # Dictionary containing the information for building storages.
        self.agentInfo = {} # Information of each Agent on the map.
        self.load(planetInfo)


    def getMapPath(self):
        print "Looking for ", self.name
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
        location = agent.instance.getLocation()
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
        It pickles the planet. (Try saying it three times)
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

        print "Loading planet: " , self.name
        for attr in content.keys():
            setattr(self, attr, content[attr])
            print attr, ": ", content[attr]

