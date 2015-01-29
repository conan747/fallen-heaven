__author__ = 'cos'


import os

from fife import fife
from fife.extensions import pychan
from fife.extensions.pychan import widgets
from fife.extensions.pychan.fife_pychansettings import FifePychanSettings

from xml.sax.saxutils import XMLGenerator
from xml.sax.xmlreader import AttributesNSImpl
# from fife.extensions.pychan.internal import get_manager


_MODE_DEFAULT, _MODE_BUILD = xrange(2)

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

    def closeExtraWindows(self):
        pass

    # def setFPSText(self, text):
    #     self._fpstext.text = text



class StrategicHUD(object):
    def __init__(self, world):
        self._world = world
        self._widget = pychan.loadXML('gui/strategic_hud.xml')
        self.buildingWidget = pychan.loadXML('gui/construction_pannel.xml')
        self.structureWidget = pychan.loadXML('gui/structure_info.xml')
        self.structureWidget.hide()
        self.buildingWidget.hide()
        self.storageUI = None

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

            if not self.selectedBuilding:
                self.onNextPressed()    # So that it displays some information.

            self._world.startBuilding(self.selectedBuilding)
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
        self._world.startBuilding(self.selectedBuilding)


    def onNextPressed(self):
        '''
        Select the previous unit.
        :return:
        '''
        self.buildingIndex += 1

        if self.buildingIndex == self.buildingList.__len__():
            self.buildingIndex = 0

        self.selectedBuilding = self.buildingList[self.buildingIndex]["buildingName"]
        if self._world.mode == _MODE_BUILD:
            self._world.startBuilding(self.selectedBuilding)

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

        if not self.buildingList:
                self.loadBuildingList()

        if not self.selectedBuilding:
            self.onNextPressed()    # So that it displays some information.

        activeUnit = None
        activeUnitID = self._world.activeUnit
        if activeUnitID:
            activeUnit = self._world.scene.instance_to_agent[activeUnitID]
            activeUnitInfo = activeUnit.properties
            print activeUnitInfo
        else:
            self.closeExtraWindows()
            return

        for info in infoDict.keys():
            # For the buildingWidget
            label = self.buildingWidget.findChild(name=info)
            buildingInfo = self.buildingList[self.buildingIndex]
            if label:
                label.text = unicode(buildingInfo[infoDict[info]])

            if activeUnitID and (activeUnit.nameSpace == "Building"):
                # For the structureWidget
                label = self.structureWidget.findChild(name=info)
                if label:
                    label.text = unicode(activeUnitInfo[infoDict[info]])
                self._world.HUD.structureWidget.show()
            else:
                print "The selected unit is not a Building!"
                self.closeExtraWindows()
                return


        ## Show storage UI if needed.
        if self.storageUI:
                self.storageUI.hide()
                self.storageUI = None

        if activeUnitID and (activeUnit.nameSpace == "Building"):
            if activeUnit.storage:
                self.storageUI = activeUnit.storage.getUI()
                self.storageUI.show()
                print "Showing production window"

    def closeExtraWindows(self):
        if self.storageUI:
            self.storageUI.hide()
            self.storageUI = None

        self.structureWidget.hide()

        print "Hiding buildingwidget"
        self.buildingWidget.hide()