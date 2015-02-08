__author__ = 'cos'


import os

from fife import fife
from fife.extensions import pychan
from fife.extensions.pychan import widgets
from fife.extensions.pychan.fife_pychansettings import FifePychanSettings

# from xml.sax.saxutils import XMLGenerator
# from xml.sax.xmlreader import AttributesNSImpl



# -----------------------------------------------------------------------------------------------------------------
#       Widget
# -----------------------------------------------------------------------------------------------------------------
class Widget(object):

    widget = None
    infoDict = {"unitName": "buildingName",
        "production" : "ProductionType",
        "energyConsumption" : "ConsummationEnergy",
        "armor" : "Hp",
        "Cost" : "Cost"
        }

    def hide(self):
        self.widget.hide()
    def show(self):
        self.widget.show()


# -----------------------------------------------------------------------------------------------------------------
#       HUD
# -----------------------------------------------------------------------------------------------------------------
class HUD(Widget):
    '''
    Parent class that will be inherited.
    '''
    def __init__(self, world):
        self.world = world

    def closeExtraWindows(self):
        pass

    def updateUI(self):
        pass


# -----------------------------------------------------------------------------------------------------------------
#       TacticalHUD
# -----------------------------------------------------------------------------------------------------------------

class TacticalHUD(HUD):
    def __init__(self, world):
        super(TacticalHUD,self).__init__(world)
        self.widget = pychan.loadXML('gui/tactical_hud.xml')

        self.widget.mapEvents({
                'nextTurnButton' : self.world.onSkipTurnPress,
                'attackLightButton' : self.world.onAttackButtonPressed
        })

        self.structureWidget = StructureWidget(self)

    def updateUI(self):
        self.structureWidget.updateUI()


# -----------------------------------------------------------------------------------------------------------------
#       ConstructingWidget
# -----------------------------------------------------------------------------------------------------------------

class ConstructingWidget(Widget):
    def __init__(self, parent):

        self.structureList = [] # List containing all the property dictionaries for the buildings
        self.structureIndex = None   #Index of the selected building in the List.
        self.buildingStructName = None    #Name of the structure that is being built.
        self.HUD = parent

        self.widget = pychan.loadXML('gui/construction_pannel.xml')
        self.hide()

        self.structureIndex = 0


        self.widget.mapEvents({
                'buttonPrevious' : self.onPreviousPressed,
                'buttonNext' : self.onNextPressed
        })

    def onPreviousPressed(self):
        '''
        Select the previous unit.
        :return:
        '''
        if self.structureIndex == 0:
            self.structureIndex = self.structureList.__len__() -1
        else:
            self.structureIndex -= 1

        self.buildingStructName = self.structureList[self.structureIndex]["buildingName"]
        self.updateUI()
        self.HUD.world.startBuilding(self.buildingStructName)


    def onNextPressed(self):
        '''
        Select the previous unit.
        :return:
        '''

        if not self.structureList:
            self.loadStructureList()

        self.structureIndex += 1

        if self.structureIndex == self.structureList.__len__():
            self.structureIndex = 0

        self.buildingStructName = self.structureList[self.structureIndex]["buildingName"]
        self.updateUI()
        self.HUD.world.startBuilding(self.buildingStructName)


    def loadStructureList(self):
        '''
        Will load the information about the buildings (what to display) form the UnitLoader.
        :return:
        '''
        allStructureProps = self.HUD.world.scene.unitLoader.buildingProps
        for structureProps in allStructureProps.values():
            if structureProps["faction"] == self.HUD.world.faction.name:
                self.structureList.append(structureProps)

        self.structureIndex = 0

    def show(self):
        # self.updateUI()
        super(ConstructingWidget, self).show()

    def updateUI(self):
        '''
        Display the proper information.
        :return:
        '''

        if not self.structureList:
            self.loadStructureList()

        buildingInfo = self.structureList[self.structureIndex]

        for info in self.infoDict.keys():
            label = self.widget.findChild(name=info)
            if label:
                label.text = unicode(buildingInfo[self.infoDict[info]])

        # self.show()



# -----------------------------------------------------------------------------------------------------------------
#       StructureWidget
# -----------------------------------------------------------------------------------------------------------------

class StructureWidget(Widget):
    def __init__(self, parent):

        self.HUD = parent

        self.widget = pychan.loadXML('gui/structure_info.xml')
        self.hide()
        self.storageWidget = None

    def updateUI(self):

        activeUnit = None
        activeUnitID = self.HUD.world.activeUnit
        activeUnitInfo = None

        if self.storageWidget:
                self.storageWidget.hide()
                self.storageWidget = None

        if not activeUnitID:
            # No unit was selected therefore hide this widget.
            self.hide()
            return

        activeUnit = self.HUD.world.scene.instance_to_agent[activeUnitID]
        activeUnitInfo = activeUnit.properties
        print activeUnitInfo

        # if activeUnit.properties.faction != self.HUD.world.faction.name:
        #     print activeUnit.properties.faction #TEST
        #     return

        if activeUnit.agentType != "Building":
            # No Building was selected therefore hide this widget.
            self.hide()
            return


        for info in self.infoDict.keys():
            label = self.widget.findChild(name=info)
            if label:
                label.text = unicode(activeUnitInfo[self.infoDict[info]])

        self.show()

        if activeUnit.storage:
            self.storageWidget = StorageUI(activeUnit.storage)
            self.storageWidget.updateUI()
            self.storageWidget.show()



# -----------------------------------------------------------------------------------------------------------------
#       StorageUI
# -----------------------------------------------------------------------------------------------------------------


class StorageUI(Widget):
    def __init__(self, storage):

        self.storage = storage # This will point at the storage object that it represents.
        self.widget = pychan.loadXML('gui/storage.xml')
        self.widget.mapEvents({
            'completeUnits': self.storage.completeUnits
        })
        self.hide()



        self.producinUnitsWidget = None
        self.availableinUnitsWidget = None


    def updateUI(self):

        ## Setup the area where the player can select units to be produced.
        # As this should not change, do it only once.
        if not self.availableinUnitsWidget:
            self.availableinUnitsWidget = self.widget.findChild(name="available_units")

            children = self.availableinUnitsWidget.findChildren()
            if children.__len__() < 2:
                for unitName in self.storage.ableToProduce:
                    vbox = pychan.widgets.VBox()
                    icon = pychan.widgets.Icon(name=unicode(unitName), image="gui/icons/boy.png")
                    def callback(arg=unitName): # Weird way of doing it. Taken from here: http://wiki.wxpython.org/Passing%20Arguments%20to%20Callbacks
                        self.storage.buildUnit(arg)

                    icon.capture(callback, event_name="mouseClicked")
                    vbox.addChild(icon)
                    label = pychan.widgets.Label(text=unicode(unitName))
                    vbox.addChild(label)
                    cost = self.storage.world.scene.unitLoader.unitProps[unitName]["Cost"]
                    label = pychan.widgets.Label(text=unicode(str(cost)))
                    vbox.addChild(label)
                    self.availableinUnitsWidget.addChild(vbox)

            self.availableinUnitsWidget.adaptLayout()

        ## Add the icons for the units that are being built:
        if not self.producinUnitsWidget:
            self.producinUnitsWidget = self.widget.findChild(name="producing_units")

        self.producinUnitsWidget.removeAllChildren()

        # Add the unit icons again.

        for iconName in self.storage.unitsReady:
            icon = pychan.widgets.Icon(name=unicode(iconName), image="gui/icons/boy.png")
            icon.background_color = (0, 255, 0, 200)
            icon.foreground_color = (0, 255, 0, 200)
            icon.base_color = (0, 255, 0, 200)
            icon.border_size = 2
            # Change icon callback to deployUnit
            print "Icon name" , iconName
            def callback(arg=iconName): # Weird way of doing it. Taken from here: http://wiki.wxpython.org/Passing%20Arguments%20to%20Callbacks
                    self.storage.deployUnit(arg) # CHECK!
            icon.capture(callback, event_name="mouseClicked")

            self.producinUnitsWidget.addChild(icon)


        for iconName in self.storage.inProduction:
            icon = pychan.widgets.Icon(name=unicode(iconName), image="gui/icons/boy.png")
            def callback(arg=iconName): # Weird way of doing it. Taken from here: http://wiki.wxpython.org/Passing%20Arguments%20to%20Callbacks
                    self.storage.cancelUnit(arg)
            icon.capture(callback, event_name="mouseClicked")

            self.producinUnitsWidget.addChild(icon)

        self.producinUnitsWidget.adaptLayout()






# -----------------------------------------------------------------------------------------------------------------
#       StrategicHUD
# -----------------------------------------------------------------------------------------------------------------
class StrategicHUD(HUD):
    def __init__(self, world):
        super(StrategicHUD, self).__init__(world)
        self.widget = pychan.loadXML('gui/strategic_hud.xml')
        self.constructionWidget = ConstructingWidget(self)
        self.structureWidget = StructureWidget(self)
        self.storageUI = None

        self.widget.mapEvents({
                'build' : self.onBuildPressed, #self.world.testBuilding
                # 'attackLightButton' : self.world.onAttackButtonPressed
        })


    def loadBuildingList(self):
        '''
        Will load the information about the buildings (what to display) form the UnitLoader.
        :return:
        '''
        allBuildingProps = self.world.scene.unitLoader.buildingProps
        for buildingProps in allBuildingProps.values():
            if buildingProps["faction"] == self.world.faction.name:
                self.buildingList.append(buildingProps)

        self.buildingIndex = 0


    def onBuildPressed(self):

        if self.world.mode != self.world.MODE_BUILD:
            if self.constructionWidget.buildingStructName:
                self.world.startBuilding(self.constructionWidget.buildingStructName)
            else:
                self.constructionWidget.onNextPressed()
        else:
            self.world.stopBuilding()


    def updateUI(self):
        '''
        Display the proper information.
        :return:
        '''

        if self.world.mode == self.world.MODE_BUILD:
            self.constructionWidget.updateUI()
            self.constructionWidget.show()
            self.structureWidget.hide() #TEST if this is necesary

        else:
            self.constructionWidget.hide() # TEST if this is necesary
            self.structureWidget.updateUI()
            # self.structureWidget.show()


    def closeExtraWindows(self):
        if self.storageUI:
            self.storageUI.hide()
            self.storageUI = None

        self.structureWidget.hide()

        print "Hiding buildingwidget"
        self.constructionWidget.hide()