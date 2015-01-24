__author__ = 'cos'


import os

from fife import fife
from fife.extensions import pychan
from fife.extensions.pychan import widgets
from fife.extensions.pychan.fife_pychansettings import FifePychanSettings

from xml.sax.saxutils import XMLGenerator
from xml.sax.xmlreader import AttributesNSImpl
# from fife.extensions.pychan.internal import get_manager


class TacticalHUD(object):
    def __init__(self, world):
        self._world = world
        self._widget = pychan.loadXML('gui/tactical_hud.xml')

        # self._image = world.engine.getImageManager().load("./gui/HUDs/combat_botton.png")
        # self._guiImage = fife.GuiImage(self._image)
        # wid = self._widget.findChild(name="high_score")
        # print wid._getName()
        # wid.setBackgroundImage(self._guiImage)
        # print "Image size:" , self._image.getWidth()
        #
        #
        #
        # print "Image size" , self._guiImage.getWidth(), self._guiImage.getHeight()

        # self._widget.position = (0, 0)
        self._widget.mapEvents({
                'nextTurnButton' : self._world.onSkipTurnPress,
                'attackLightButton' : self._world.onAttackButtonPressed
        })


    def show(self):
        self._widget.show()

    def hide(self):
        self._widget.hide()

    # def setFPSText(self, text):
    #     self._fpstext.text = text



class StrategicHUD(object):
    def __init__(self, world):
        self._world = world
        self._widget = pychan.loadXML('gui/strategic_hud.xml')
        self.buildingWidget = pychan.loadXML('gui/construction_pannel.xml')
        self.buildingWidget.hide()

        self.buildingList = [] # List containing all the property dictionaries for the buildings
        self.buildingIndex = None   #Index of the selected building in the List.
        self.selectedBuilding = None    #Name of the selected building.

        # self._image = world.engine.getImageManager().load("./gui/HUDs/combat_botton.png")
        # self._guiImage = fife.GuiImage(self._image)
        # wid = self._widget.findChild(name="high_score")
        # print wid._getName()
        # wid.setBackgroundImage(self._guiImage)
        # print "Image size:" , self._image.getWidth()
        #
        #
        #
        # print "Image size" , self._guiImage.getWidth(), self._guiImage.getHeight()

        # self._widget.position = (0, 0)
        self._widget.mapEvents({
                'build' : self.onBuildPressed, #self._world.testBuilding
                # 'attackLightButton' : self._world.onAttackButtonPressed
        })

        self.buildingWidget.mapEvents({
                'buttonPrevious' : self.onPreviousPressed,
                'buttonNext' : self.onNextPressed
        })


    def show(self):
        self._widget.show()

    def hide(self):
        self._widget.hide()

    def loadBuildingList(self):
        '''
        Will load the information about the buildings (what to display) form the UnitLoader.
        :return:
        '''
        allBuildingProps = self._world.scene.unitLoader.buildingProps
        for buildingProps in allBuildingProps.values():
            if buildingProps["faction"] == "Human": ## FIXME: make this variable
                self.buildingList.append(buildingProps)

        self.buildingIndex = 0


    def onBuildPressed(self):
        if not self.buildingList:
            self.loadBuildingList()

        if not self.buildingWidget.isVisible():
            self.buildingWidget.show()
            self._world.startBuilding()
            self.onNextPressed()
        else:
            self.buildingWidget.hide()
            self._world.stopBuilding()

    def onPreviousPressed(self):
        '''
        Select the previous unit.
        :return:
        '''
        if self.buildingIndex == 0:
            self.buildingIndex = self.buildingList.__len__() -1
        else:
            self.buildingIndex -= 1

        self.selectedBuilding = self.buildingList[self.buildingIndex]["buildingName"]
        self.updateUI()

    def onNextPressed(self):
        '''
        Select the previous unit.
        :return:
        '''
        self.buildingIndex += 1

        if self.buildingIndex == self.buildingList.__len__():
            self.buildingIndex = 0

        self.selectedBuilding = self.buildingList[self.buildingIndex]["buildingName"]
        self.updateUI()


    def updateUI(self):
        '''
        Display the proper information.
        :return:
        '''
        infoDict = {"unitName": "buildingName",
        "production" : "ProductionType",
        "energyConsumption" : "ConsummationEnergy",
        "armor" : "Hp",
        "Cost" : "Cost"
        }

        for info in infoDict.keys():
            label = self.buildingWidget.findChild(name=info)
            buildingInfo = self.buildingList[self.buildingIndex]
            label.text = unicode(buildingInfo[infoDict[info]])

