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

    def hide(self, free=False):
        self.widget.hide(free)
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

    def adjustPos(self):
        '''
        Adjusts the widget position to match the screen resolution.
        :return:
        '''
        defaultSize = (1024., 768.)

        # Get the size of the window:
        engineSettings = self.world.universe._engine.getSettings()
        screenSize = (engineSettings.getScreenWidth(), engineSettings.getScreenHeight())

        coef = (screenSize[0] / defaultSize[0], screenSize[1] / defaultSize[1])

        pos = self.widget.getAbsolutePos()

        self.widget._setX(int(pos[0] * coef[0]))
        self.widget._setY(int(pos[1] * coef[1]))



# -----------------------------------------------------------------------------------------------------------------
#       TacticalHUD
# -----------------------------------------------------------------------------------------------------------------

class TacticalHUD(HUD):


    LWEAPON, HWEAPON = xrange(2)

    def __init__(self, world):
        super(TacticalHUD,self).__init__(world)
        self.widget = pychan.loadXML('gui/tactical_hud.xml')

        self.widget.mapEvents({
                'nextTurnButton' : self.world.onSkipTurnPress,
                'attackLightButton' : self.onAttackLightPressed,
                'attackHeavyButton' : self.onAttackHeavyPressed
        })

        self.structureWidget = StructureWidget(self)
        self.unitInfoWidget = UnitInfoWidget(self)

        self.adjustPos()

    def onAttackLightPressed(self):
        self.world.onAttackButtonPressed(self.LWEAPON)

    def onAttackHeavyPressed(self):
        self.world.onAttackButtonPressed(self.HWEAPON)

    def destroy(self):
        self.widget.hide()
        self.widget.mapEvents({
                'nextTurnButton' : None,
                'attackLightButton' : None
        })
        del self.widget
        self.structureWidget.destroy()


    def updateUI(self):
        self.structureWidget.updateUI()
        unit = self.world.getActiveAgent()
        self.unitInfoWidget.updateUI(unit, world=self.world)


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

    def destroy(self):
        self.widget.hide()

        self.widget.mapEvents({
                'buttonPrevious' : None,
                'buttonNext' : None
        })
        del self.widget


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
                if not "CanBuild" in structureProps.keys():
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

        ## Display the proper image:
        imageContainer = self.widget.findChild(name="imageContainer")
        imageWidget = None
        imageWidget = imageContainer.findChildByName("image")
        if imageWidget:
            imageContainer.removeChild(imageWidget)
        buildingName = buildingInfo["buildingName"]
        imageFile = "objects/agents/buildings/" + buildingName + ".png"
        imageWidget = pychan.Icon(parent=imageContainer, name="image", image=imageFile )
        imageContainer.addChild(imageWidget)
        self.widget.adaptLayout()



# -----------------------------------------------------------------------------------------------------------------
#       StructureWidget
# -----------------------------------------------------------------------------------------------------------------

class StructureWidget(Widget):


    def __init__(self, parent):

        self.HUD = parent

        self.widget = pychan.loadXML('gui/structure_info.xml')
        self.hide()
        self.storageWidget = None

    def destroy(self):
        self.hide()
        if self.storageWidget:
            self.storageWidget.destroy()
        self.widget.removeAllChildren()
        del self.widget

    def updateUI(self):

        activeUnit = self.HUD.world.getActiveAgent()

        if self.storageWidget:
                self.storageWidget.hide(free=True)
                self.storageWidget = None

        if not activeUnit:
            # No unit was selected therefore hide this widget.
            self.hide()
            return

        activeUnitInfo = activeUnit.properties

        # for info in activeUnitInfo.items():
        #  print "\t%s : %s" % info

        if activeUnit.agentType != "Building":
            # No Building was selected therefore hide this widget.
            self.hide()
            return

        ## Display the proper image:
        imageContainer = self.widget.findChild(name="imageContainer")
        imageWidget = None
        imageWidget = imageContainer.findChildByName("image")
        if imageWidget:
            imageContainer.removeChild(imageWidget)
        buildingName = activeUnitInfo["buildingName"]
        imageFile = "objects/agents/buildings/" + buildingName + ".png"
        imageWidget = pychan.Icon(parent=imageContainer, name="image", image=imageFile )
        imageContainer.addChild(imageWidget)

        actionButton = self.widget.findChildByName("action")
        if activeUnit.action:
            actionButton.capture(activeUnit.action)
            actionButton.show()
        else:
            actionButton.hide()

        self.widget.adaptLayout()


        # self.widget.distributeData(self.infoDict)

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
            'completeUnits': self.completeUnits
        })
        self.hide()

        self.producinUnitsWidget = None
        self.availableinUnitsWidget = None

    def completeUnits(self):
        self.storage.completeUnits()

    def destroy(self):
        self.widget.mapEvents({
            'completeUnits': None
        })

        children = self.widget.findChildren(parent=self.widget)
        for widget in children:
            widget.capture(callback=None, event_name="mouseClicked")

        self.widget.hide()
        del self.widget




    def updateUI(self):

        ## Setup the area where the player can select units to be produced.
        # As this should not change, do it only once.

        print "At this point the storage contains: "
        print "In production: " , self.storage.inProduction
        print "Ready: ", self.storage.unitsReady


        if not self.availableinUnitsWidget and self.storage.ableToProduce:
            self.availableinUnitsWidget = self.widget.findChild(name="available_units")

            children = self.availableinUnitsWidget.findChildren()
            if children.__len__() < 2:
                for unitName in self.storage.ableToProduce:
                    vbox = pychan.widgets.VBox()
                    imageName = "gui/icons/boy.png"
                    if os.path.isfile("objects/agents/units/" + unitName + ".png"):
                        imageName = "objects/agents/units/" + unitName + ".png"
                    icon = pychan.widgets.Icon(name=unicode(unitName), image=imageName)
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



        for widget in self.producinUnitsWidget.findChildren(parent=self):
            widget.capture(callback=None, event_name="mouseClicked")
        self.producinUnitsWidget.removeAllChildren()

        # Add the unit icons again.

        for iconName in self.storage.unitsReady:
            imageName = "gui/icons/boy.png"
            unitName = iconName.split(":")[1]
            if os.path.isfile("objects/agents/units/" + unitName + ".png"):
                imageName = "objects/agents/units/" + unitName + ".png"
            icon = pychan.widgets.Icon(name=unicode(iconName), image=imageName)
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
            imageName = "gui/icons/boy.png"
            unitName = iconName.split(":")[1]
            if os.path.isfile("objects/agents/units/" + unitName + ".png"):
                imageName = "objects/agents/units/" + unitName + ".png"
            icon = pychan.widgets.Icon(name=unicode(iconName), image=imageName)
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
        self.topWidget = pychan.loadXML('gui/topWidget.xml')
        self.topWidget.show()

        self.widget.mapEvents({
                'build' : self.onBuildPressed, #self.world.testBuilding
                'toUniverseButton' : self.world.backToUniverse,
                'recycle' : self.onRecyclePressed
        })

        self.adjustPos()

        self.updateUI()

    def show(self):
        self.widget.show()
        self.topWidget.show()


    def destroy(self):

        self.widget.mapEvents({
                'build' : None,
                'toUniverseButton' : None
        })

        self.widget.hide()
        del self.widget
        self.constructionWidget.destroy()
        self.structureWidget.destroy()

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


    def onRecyclePressed(self):

        if self.world.mode != self.world.MODE_RECYCLE:
            self.world.startRecycling()
        else:
            self.world.setMode(self.world.MODE_DEFAULT)

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

        # Update Credits:
        creditLabel = self.topWidget.findChildByName("totalCredits")
        credits = self.world.faction.resources["Credits"]
        creditLabel.text = unicode(str(credits))

        self.topWidget.adaptLayout()


    def closeExtraWindows(self):
        # if self.storageUI:
        #     self.storageUI.hide()
        #     self.storageUI = None

        self.structureWidget.hide()

        print "Hiding buildingwidget"
        self.constructionWidget.hide()




# -----------------------------------------------------------------------------------------------------------------
#       StorageUI
# -----------------------------------------------------------------------------------------------------------------

class UnitInfoWidget(Widget):
    '''
    In the tactical HUD shows the unit information.
    '''

    def __init__(self, unit=None):
        self.widget = pychan.loadXML("gui/unit_info.xml")
        self.unit = unit

        self.nameLabel = self.widget.findChildByName("unitName")

        self.HPLabel = self.widget.findChildByName("HPLabel")
        self.HPBar = self.widget.findChildByName("HPBar")

        self.APLabel = self.widget.findChildByName("APLabel")
        self.APBar = self.widget.findChildByName("APBar")
        self.attackBar = self.widget.findChildByName("attackBar")
        
        self.attackLabel = self.widget.findChildByName("attackName")
        self.damageLabel = self.widget.findChildByName("damage")
        self.rangeLabel = self.widget.findChildByName("range")

    def updateUI(self, unit=None, world=None):


        self.unit = unit

        if not self.unit:
            print "Error, no unit selected!"
            self.widget.hide()
            return

        if unit.agentType == "Building":
            return

        self.nameLabel.text = unicode(unit.unitName)

        currentHP = unit.health
        maxHP = unit.properties["Hp"]
        self.HPLabel.text = u"%d/%d" % (currentHP, maxHP)
        HPPercentage = 100 * currentHP/maxHP
        self.HPBar.value = HPPercentage

        currentAP = unit.AP
        maxAP = unit.properties["TimeUnits"]
        self.APLabel.text = u"%d/%d" % (currentAP, maxAP)
        APPercentage = 100 * currentAP/maxAP
        self.APBar.value = APPercentage
        self.widget.show()

        if world:
            if world.mode == world.MODE_ATTACK:
                if world.attackType == unit.LWEAPON:
                    weaponprops = unit.lightWeapon.properties
                else:
                    weaponprops = unit.heavyWeapon.properties

                self.attackBar.value = weaponprops["PercentTimeUnits"]
                self.attackLabel.text = unicode(weaponprops["Name"])
                self.damageLabel.text = u"Dmg: %d" % weaponprops["DamageContact"]
                self.rangeLabel.text = u"Rng: %d" % weaponprops["Range"]
            else:
                self.attackBar.value = 0

                self.attackLabel.text = u""
                self.damageLabel.text = u""
                self.rangeLabel.text = u""
