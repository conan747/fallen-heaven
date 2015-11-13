# -*- coding: utf-8 -*-

# ####################################################################
#  Copyright (C) 2005-2013 by the FIFE team
#  http://www.fifengine.net
#  This file is part of FIFE.
#
#  FIFE is free software; you can redistribute it and/or
#  modify it under the terms of the GNU Lesser General Public
#  License as published by the Free Software Foundation; either
#  version 2.1 of the License, or (at your option) any later version.
#
#  This library is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#  Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public
#  License along with this library; if not, write to the
#  Free Software Foundation, Inc.,
#  51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
# ####################################################################

from fife import fife
import math, random
from fife.extensions import pychan
from fife.extensions.pychan import widgets
from fife.extensions.pychan.internal import get_manager

from scripts.common.eventlistenerbase import EventListenerBase
from fife.extensions.soundmanager import SoundManager
# from agents.hero import Hero
# from agents.girl import Girl
# from agents.cloud import Cloud
from agents.unit import *
from fife.extensions.fife_settings import Setting

from gui.huds import TacticalHUD
from combat import Trajectory
from gui.dialogs import InfoDialog
from view import View
from unitManager import *
from combatManager import *

TDS = Setting(app_name="rio_de_hola")





class WorldListener(fife.IKeyListener, fife.IMouseListener):
    """
    Main game listener.  Listens for Mouse and Keyboard events.

    This class also has the ability to attach and detach itself from
    the event manager in cases where you do not want input processed (i.e. when
    the main menu is visible).  It is NOT attached by default.
    """

    def __init__(self, world):
        self._engine = world.engine
        self._world = world
        self._settings = world.settings
        self._eventmanager = self._engine.getEventManager()

        fife.IMouseListener.__init__(self)
        fife.IKeyListener.__init__(self)

        self.ctrldown = False

        self._attached = False
        self._cellSelectionRenderer = None
        self.unitManager = None

        self._lastmousepos = (0.0, 0.0)

    def attach(self):
        """
        Attaches to the event manager.
        """
        if not self._attached:
            # self._world.keystate.reset()
            self._eventmanager.addMouseListenerFront(self)
            self._eventmanager.addKeyListenerFront(self)
            self._attached = True

    def detach(self):
        """
        Detaches from the event manager.
        """
        if self._attached:
            self._eventmanager.removeMouseListener(self)
            self._eventmanager.removeKeyListener(self)
            self._attached = False

    def cycleThroughInstances(self, instances):
        '''
        Checks what instances are under the cursor and selects the unselected one.
        '''
        if not instances:
            return

        id=0
        ids = [instance.getFifeId() for instance in instances]
        if self._world.activeUnit:
            activeID = self._world.activeUnit
            if activeID in ids:
                if len(ids) > 1:
                    ids.sort()
                    id = ids[ids.index(activeID) -1] #Cycle through the instances
        if id == 0:
            id = ids[0]


        if self._world.factionUnits:
            if id in self._world.factionUnits[self._world.currentTurn]:
                print "Instance: " , id, " is owned by this player!"
                self._world.selectUnit(id)
            else:
                return

        if not self.unitManager:
            self.unitManager = self._world.unitManager

        print "Instance: ", id
        if id in self.unitManager.getFifeIds():
            self._world.selectUnit(id)
            print "Agent Name: " , self.unitManager.getAgent(id).agentName



    def clickDefault(self, clickpoint):
        # self.hide_instancemenu()

        initialUnit = self._world.activeUnit

        instances = self._world.getInstancesAt(clickpoint)

        print "selected instances on agent layer: ", [i.getObject().getId() for i in instances]
        print "Found " , instances.__len__(), "instances"

        self.cycleThroughInstances(instances)

        if not self.unitManager:
            self.unitManager = self._world.unitManager

        if self._world.activeUnit:
            if self._world.activeUnit == initialUnit:
                self._world.getActiveAgent().teleport(self._world.getLocationAt(clickpoint))


    def clickGetIn(self, clickpoint):
        # self.hide_instancemenu()

        if not self._world.activeUnit:
            return
        else:
            activeUnit = self._world.getActiveAgent()
            if activeUnit.agentType == "Building":
                return

        instances = self._world.getInstancesAt(clickpoint)
        print "selected instances on agent layer: ", [i.getObject().getId() for i in instances]
        print "Found " , instances.__len__(), "instances"

        if not self.unitManager:
            self.unitManager = self._world.unitManager

        for instance in instances:
            clickedAgent = self.unitManager.getAgent(instance)
            if clickedAgent and clickedAgent.agentType == "Building":
                storage = clickedAgent.storage
                if storage:
                    ##HACK: only accept on dropships
                    if clickedAgent.properties["StructureCategory"] == "Dropship":
                        if storage.addUnit(activeUnit):
                            ## storage added correctly -> remove unit from the map.
                            activeUnit.die()
                            self._world.selectUnit(None)



    def clickDeploy(self, clickpoint):
        '''

        '''
        unit = self._world.deploying

        clickLocation = self._world.getLocationAt(clickpoint)
        if not unit.teleport(clickLocation):
            # This is supposed to be an ilegal teleport position -> cancel
            self.cancelDeploy()
            return

        if not self.unitManager:
            self.unitManager = self._world.unitManager

        # Generate an instance for the unit.
        self.unitManager.addAgent(unit, clickLocation)
        self._world.storage.unitDeployed()
        self.cancelDeploy()

    def cancelDeploy(self):
        self._world.deploying = None
        self._world.storage = None
        self._world.setMode(self._world.MODE_DEFAULT)

    def clickBuild(self, clickpoint):
        buildingCost = int(self._world.construction.properties["Cost"])
        if self._world.deductCredits(buildingCost):
            if not self.placeBuilding(clickpoint):
                self._world.deductCredits(-buildingCost)
        ## TODO: Give feedback of why it can't be built.


    def placeBuilding(self, clickpoint):
        '''
        Locate the building at clickpoint.
        '''
        # We don't need to do anything since the instance should be here already.
        location = self._world.getLocationAt(clickpoint)
        construction = self._world.construction
        print "Agent Type: " , construction.agentType

        if construction.teleport(location):
            self._world.addBuilding(self._world.construction)
            self._world.construction = None
            self._world.cursorHandler.setCursor(self._world.cursorHandler.CUR_DEFAULT)
            self._world.setMode(self._world.MODE_DEFAULT)
            self._world.stopBuilding()
            return True

        return False
        ## TODO: If we are building a wall then don't close the builder widget.




    def mousePressed(self, evt):
        if evt.isConsumedByWidgets():
            return

        clickpoint = fife.ScreenPoint(evt.getX(), evt.getY())
        if (evt.getButton() == fife.MouseEvent.LEFT):
            if self._world.mode == self._world.MODE_DEFAULT:
                self.clickDefault(clickpoint)
            elif self._world.mode == self._world.MODE_ATTACK:
                self.clickAttack(clickpoint)
            elif self._world.mode == self._world.MODE_DEPLOY:
                self.clickDeploy(clickpoint)
            elif self._world.mode == self._world.MODE_BUILD:
                self.clickBuild(clickpoint)
            elif self._world.mode == self._world.MODE_RECYCLE:
                self.clickRecycle(clickpoint)
            elif self._world.mode == self._world.MODE_GET_IN:
                self.clickGetIn(clickpoint)

        if (evt.getButton() == fife.MouseEvent.RIGHT):

            if self._world.mode == self._world.MODE_BUILD:
                self._world.stopBuilding()
            elif  self._world.mode == self._world.MODE_ATTACK:
                if self._world.activeUnitRenderer:
                    self._world.activeUnitRenderer.removeAllColored()
            else:
                self._world.selectUnit(None)
            self._world.HUD.closeExtraWindows()
            self._world.setMode(self._world.MODE_DEFAULT)
            # self._world.handleCursor()



    def mouseMoved(self, evt):

        self._world.mousePos = (evt.getX(), evt.getY())

        if self._world.mode == self._world.MODE_DEFAULT:
            if not self._cellSelectionRenderer:
                if self._world.cameras:
                    camera = self._world.cameras['main']
                    self._cellSelectionRenderer = fife.CellSelectionRenderer.getInstance(camera)
                    self._cellSelectionRenderer.setEnabled(True)
                    self._cellSelectionRenderer.activateAllLayers(self._world.map)

            if self._cellSelectionRenderer:
                mousePoint = fife.ScreenPoint(evt.getX(), evt.getY())
                self._cellSelectionRenderer.reset()
                location = self._world.getLocationAt(mousePoint)
                self._cellSelectionRenderer.selectLocation(location)

    def mouseReleased(self, event):
        pass

    def mouseEntered(self, event):
        pass

    def mouseExited(self, event):
        pass

    def mouseClicked(self, event):
        pass

    def mouseWheelMovedUp(self, evt):
        if self.ctrldown:
            self._world.cameras['main'].setZoom(self._world.cameras['main'].getZoom() * 1.05)

    def mouseWheelMovedDown(self, evt):
        if self.ctrldown:
            self._world.cameras['main'].setZoom(self._world.cameras['main'].getZoom() / 1.05)

    def mouseDragged(self, event):
        pass
    #     if event.isConsumedByWidgets():
    #         return
    #
    #     clickpoint = fife.ScreenPoint(event.getX(), event.getY())
    #     if (event.getButton() == fife.MouseEvent.LEFT):
    #         if clickpoint.x > self._lastmousepos[0] + 5 or clickpoint.x < self._lastmousepos[0] - 5 or clickpoint.y > \
    #                         self._lastmousepos[1] + 5 or clickpoint.y < self._lastmousepos[1] - 5:
    #             self._world.player.walk(self._world.getLocationAt(clickpoint))
    #
    #         self._lastmousepos = (clickpoint.x, clickpoint.y)

    def keyPressed(self, evt):
        keyval = evt.getKey().getValue()
        keystr = evt.getKey().getAsString().lower()
        if keystr == 't':
            r = self._world.cameras['main'].getRenderer('GridRenderer')
            r.setEnabled(not r.isEnabled())
        elif keystr == 'c':
            r = self._world.cameras['main'].getRenderer('CoordinateRenderer')
            r.setEnabled(not r.isEnabled())
        elif keystr == 's':
            c = self._world.cameras['small']
            c.setEnabled(not c.isEnabled())
        elif keystr == 'r':
            self._world.model.deleteMaps()
            self._world.load(self.filename)
        elif keystr == 'f':
            renderer = fife.CellRenderer.getInstance(self._world.cameras['main'])
            renderer.setEnabledFogOfWar(not renderer.isEnabledFogOfWar())
            self._worldcameras['main'].refresh()
        elif keystr == 'o':
            self._world.target_rotation = (self._world.target_rotation + 90) % 360
        elif keystr == '2':
            self._world.lightIntensity(0.1)
        elif keystr == '1':
            self._world.lightIntensity(-0.1)
        elif keystr == '5':
            self._world.lightSourceIntensity(25)
        elif keystr == 'n':
            self._world.nextTurn()
        elif keystr == 'a':
            self._world.onAttackButtonPressed()
        elif keystr == '4':
            self._world.lightSourceIntensity(-25)
        elif keystr == '0' or keystr == fife.Key.NUM_0:
            if self.ctrldown:
                self._world.cameras['main'].setZoom(1.0)
        elif keyval in (fife.Key.LEFT_CONTROL, fife.Key.RIGHT_CONTROL):
            self.ctrldown = True
            self._world.setMode(self._world.MODE_GET_IN)
        # if keyval == fife.Key.ESCAPE:
        #     self.detach()
        #     self._world.guicontroller.showMainMenu()
        #     event.consume()
        # self._world.keystate.updateKey(keyval, True)


    def keyReleased(self, evt):
        keyval = evt.getKey().getValue()
        if keyval in (fife.Key.LEFT_CONTROL, fife.Key.RIGHT_CONTROL):
            self.ctrldown = False
            self._world.setMode(self._world.MODE_DEFAULT)





class CursorHandler(object):
    '''
    Handles the information for the cursor.
    '''


    CUR_DEFAULT, CUR_ATTACK, CUR_CANNOT, CUR_RECYCLE, CUR_GET_IN = xrange(5)

    def __init__(self, imageManager, cursor):
        self._imageManager = imageManager
        self._cursor = cursor

        normalCursor = imageManager.load("/gui/pointers/normal_pointer.png")

        cursorAttack = imageManager.load("/gui/pointers/image0000.png")
        cursorAttack.setXShift(-32)
        cursorAttack.setYShift(-32)

        cannot = imageManager.load("/gui/pointers/image0009.png")
        cannot.setXShift(-32)
        cannot.setYShift(-32)

        recycle = imageManager.load("/gui/pointers/recycle.png")
        recycle.setXShift(-32)
        recycle.setYShift(-32)

        getIn = imageManager.load("/gui/pointers/getIn.png")
        getIn.setXShift(-32)
        getIn.setYShift(-32)



        self.cursorDict = {self.CUR_DEFAULT: normalCursor,
                           self.CUR_ATTACK: cursorAttack,
                           self.CUR_CANNOT: cannot,
                           self.CUR_RECYCLE : recycle,
                           self.CUR_GET_IN : getIn}

        self.setCursor(self.CUR_DEFAULT)

    def setCursor(self, cursorId):
        cursorImg = self.cursorDict[cursorId]
        self._cursor.set(cursorImg)



class World(object):
    """
    The world!
    Keeps track of all game objects.

    This is the meat and potatoes of the game.  This class takes care of all the units.

    This class handles:
      setup of map view (cameras ...)
      loading the scene
    """

    MODE_DEFAULT, MODE_ATTACK, MODE_DROPSHIP, MODE_DEPLOY, MODE_BUILD, MODE_RECYCLE, MODE_GET_IN = xrange(7)


    def __init__(self, universe, planet):

        ## Higher instances than this
        self.universe = universe
        self.engine = universe._engine
        self.eventmanager = self.engine.getEventManager()
        self.model = self.engine.getModel()
        self.settings = universe._settings

        ## Player and unit attributes
        self.planet = planet
        self.faction = universe.faction
        self._player1 = True
        self._player2 = False

        ## There can only be one world -> assign unitLoader to this world.
        self.unitManager = None
        self.unitLoader = self.universe.unitLoader
        self.unitLoader.setWorld(self)
        self.projectileGraveyard = None
        self.unitGraveyard = None
        #self.retaliation = None
        self.factionUnits = {}      ## This will hold the units for each faction.
        self.storage = None # Points at the storage object in Deploy mode.
        self.deploying = None
        self.agentLayer = None

        ## gui and widgets
        self.instancemenu = None
        self.dynamic_widgets = {}
        self.activeUnitRenderer = None
        self.cursorHandler = CursorHandler(self.engine.getImageManager(), self.engine.getCursor())

        ##Camera and visuals
        self.view = View(self, self.engine)
        self.mousePos = (100,100)   ## this is used to move the camera. Alternative method possible!
        ## Constants
        self._camMoveMargin = 20
        self._camMoveSpeed = 0.2
        self.light_intensity = 1
        self.light_sources = 0
        self.lightmodel = int(TDS.get("FIFE", "Lighting"))

        ##Sound:
        self.sound = self.universe.sound
        self.music = None

        ## Game state
        self.activeUnit = None      ## Will point at the active unit "Agent" ID.
        self.mode = self.MODE_DEFAULT
        self.busy = False

        ## Other. Possibly remove.
        self.filename = ''
        self.pump_ctr = 0 # for testing purposes
        self.ctrldown = False
        self.attackType = None

        ## To be overriden:
        self.listener = None



    def destroy(self):
        """
        Removes all objects from the scene and deletes them from the layer.
        """
        self.unitManager.destroy()


    def getActiveAgent(self):
        '''
        Returns the active agent.
        :return: Agent
        '''
        if self.activeUnit:
            return self.unitManager.getAgent(self.activeUnit)


    def moveCamera(self, speedVector):
        self.view.moveCamera(speedVector)



    def load(self, filename):
        """
        Load a xml map and setup agents and cameras.
        """

        self.filename = filename

        #Here goes the code that would load the scene.
        loader = fife.MapLoader(self.engine.getModel(),
                                self.engine.getVFS(),
                                self.engine.getImageManager(),
                                self.engine.getRenderBackend())

        if not loader.isLoadable(filename):
            print "Problem loading map: map file is not loadable"
            return

        self.map = loader.load(filename)

        self.map.initializeCellCaches()
        self.map.finalizeCellCaches()

        self.agentLayer = self.map.getLayer('TechdemoMapGroundObjectLayer')

        self.unitManager = UnitManager()

        self.initView(self.map)
        self.initAgents()

        self.unitGraveyard = UnitGraveyard(self.agentLayer)

        if int(self.settings.get("FIFE", "PlaySounds")):

            if int(self.settings.get("FIFE", "PlayMusic")):
                # play track as background music
                self.music = self.sound.soundmanager.createSoundEmitter('music/fallen.ogg')
                self.music.looping = True
                self.music.gain = 128.0
                self.music.play()

            # self.waves = self.soundmanager.createSoundEmitter('sounds/waves.ogg')
            # self.waves.looping = True
            # self.waves.gain = 16.0
            # self.waves.play()

    def initAgents(self):
        """
        Setup agents.

        Loads the "agents" (i.e. units and structures) from the planet object and initialises them.
        """

        agentList = self.planet.agentInfo
        self.unitManager.initAgents(self.map, agentList, self.unitLoader, self.planet)
        self.planet.agentInfo = {}

        if self.listener:
            self.listener.attach()
        # self._music = self._soundmanager.createSoundEmitter("music/waynesmind2.ogg")
        # self._music.callback = self.musicHasFinished
        # self._music.looping = True
        # self._soundmanager.playClip(self._music)


    def initView(self, map):
        self.view.load(map)
        self.cameras = self.view.cameras


    def updatePlanetAgents(self):
        '''
        Updates the agent information (units and structures) that the planet object stores.
        :return:
        '''
        self.unitManager.saveAllAgents(self.planet)


    def getStorageDicts(self):
        '''
        Return a dictionary containing the storages of the buildings in this scene.
        :return:
        '''
        return self.unitManager.getStorageDicts()


    def unitDied(self, fifeID):
        '''
        Process the destruction of a unit
        :param fifeID: ID of the destroyed unit
        :return:
        '''
        self.unitManager.removeInstance(fifeID)


    def getInstancesAt(self, arg):
        """
        Query the main camera for instances on our active(agent) layer.
        :param arg: Location or Point3D.
        :return: List of instance IDs.
        """
        location = None
        if isinstance(arg, fife.ScreenPoint):
            instances = self.cameras['main'].getMatchingInstances(arg, self.agentLayer, False)
            if instances:
                return instances
            else:
                location = self.getLocationAt(arg)

        elif isinstance(arg, fife.Point3D):
            point3d = arg

        elif isinstance(arg, fife.Location):
            location = arg

        if not location:
            location = fife.Location(self.agentLayer)
            location.setLayerCoordinates(point3d)

        return self.agentLayer.getInstancesAt(location, False)


    def getLocationAt(self, clickpoint):
        """
        Query the main camera for the Map location (on the agent layer)
        that a screen point refers to.
        :return: Location on agent Layer
        """
        target_mapcoord = self.cameras['main'].toMapCoordinates(clickpoint, False)
        target_mapcoord.z = 0
        location = fife.Location(self.agentLayer)
        location.setMapCoordinates(target_mapcoord)
        return location



    def selectUnit(self, id):
        '''
        Selects a unit and puts it as the activeUnit.
        :param id: of a unit
        :return:
        '''

        ## Create an InstanceRenderer if not existing
        if not self.activeUnitRenderer:
            self.activeUnitRenderer = self.view.renderer["InstanceRenderer"]

        ## Clear previously selected unit
        if self.activeUnit != id:
            if self.activeUnit:
                activeAgent = self.unitManager.getAgent(self.activeUnit)
                if activeAgent:
                    self.activeUnitRenderer.removeOutlined(activeAgent.instance)

        self.activeUnit = id
        if id:
            instance = self.unitManager.getAgent(id).instance
            self.activeUnitRenderer.addOutlined(instance, 173, 255, 47, 2)

        # Update UI:
        self.HUD.updateUI()


    def onSkipTurnPress(self):
        print "Skipping turn!"

        if not self._nextTurnWindow:
            self._nextTurnWindow = InfoDialog(title="Next turn")


        text = "This is the turn of"
        if not self.currentTurn:
            text += " Player 1"
        else:
            text += " Player 2"
        self._nextTurnWindow.setText(text)
        self._nextTurnWindow.show()

        self.nextTurn()

    def pump(self):
        """
        Called every frame.
        """

        # self.collectGarbage()
        # print "Start pumping world"

        engineSettings = self.engine.getSettings()
        ## Could be optimized by using engine.getCursor() and checking the cursor position.

        ## Move camera if needed:
        if self.mousePos[0] < self._camMoveMargin:
            speedVector = (-self._camMoveSpeed, -self._camMoveSpeed)
            # speedVector = (speedVector[0] * math.cos
            self.moveCamera(speedVector)

        if self.mousePos[0] > (engineSettings.getScreenWidth()-self._camMoveMargin):
            speedVector = (self._camMoveSpeed,self._camMoveSpeed)
            self.moveCamera(speedVector)

        if self.mousePos[1] < self._camMoveMargin:
            speedVector = (self._camMoveSpeed,-self._camMoveSpeed)
            self.moveCamera(speedVector)

        if self.mousePos[1] > (engineSettings.getScreenHeight()-self._camMoveMargin):
            speedVector = (-self._camMoveSpeed , self._camMoveSpeed)
            self.moveCamera(speedVector)

        #self.changeRotation()
        self.pump_ctr += 1

        ## handle mouse:
        self.handleCursor()

        # if self.activeUnit:
        #     projectile = self.unitManager.getAgent(self.activeUnit).projectile
        #     if projectile:
        #         projectile.move()
        #         self.unitManager.getAgent(self.activeUnit).projectile = None



        # print "End pumping world"

    def cleanGraveyard(self):
        '''
        Deletes the instances that are in the graveyard.
        :return:
        '''

        while self.unitGraveyard:
            unitID = self.unitGraveyard.pop()
            self.view.removePathVisual(self.unitManager.getAgent(unitID).instance)

            self.unitManager.removeInstance(unitID)

            for factionName in self.factionUnits.keys():
                if unitID in self.factionUnits[factionName]:
                    self.factionUnits[factionName].remove(unitID)
                    if self.activeUnit == unitID:
                        self.selectUnit(None)
                    print "Cleaned unit: ", unitID


    def setMode(self, mode):
        '''
        Sets the current runtime tactical mode.
        :param mode: MODE_DEFAULT, MODE_ATTACK, MODE_DROPSHIP, MODE_DEPLOY
        :return:
        '''

        if self.mode == self.MODE_ATTACK:
            renderer = fife.GenericRenderer.getInstance(self.cameras["main"])
            renderer.removeAll("LineOfSight")

        self.mode = mode
        if mode == self.MODE_BUILD:
            self.listener._cellSelectionRenderer.setEnabled(False)

        self.handleCursor()
        self.HUD.updateUI()


    def handleCursor(self):
        '''
        Changes the cursor according to the mode.
        :return:
        '''
        if self.busy:
            return

        if self.mode == self.MODE_ATTACK:
            if not self.activeUnit:
                return

            mousepoint = fife.ScreenPoint(self.mousePos[0], self.mousePos[1])
            mouseLocation = self.getLocationAt(mousepoint)

            trajectory = Trajectory( self.getActiveAgent(), self, self.attackType)
            # print "Is is reachable?"
            if trajectory.canShoot(mouseLocation, display=True):
                self.cursorHandler.setCursor(self.cursorHandler.CUR_ATTACK)
            else:
                self.cursorHandler.setCursor(self.cursorHandler.CUR_CANNOT)

        elif self.mode == self.MODE_RECYCLE:
            self.cursorHandler.setCursor(self.cursorHandler.CUR_RECYCLE)
        elif self.mode == self.MODE_GET_IN:
            self.cursorHandler.setCursor(self.cursorHandler.CUR_GET_IN)
        else:
            self.cursorHandler.setCursor(self.cursorHandler.CUR_DEFAULT)

    def backToUniverse(self):
        '''
        Goes back to the universe view.
        :return:
        '''
        self.universe.backToUniverse()


    def deductCredits(self, cred):
        '''
        Deducts the number of credits from the resources.
        :param cred: Number of credits to be reduced.
        :return: Bool saying if it was successfull (if there were enough credits)
        '''

        currentCredits = self.faction.resources["Credits"]
        if cred <= currentCredits:
            self.faction.resources["Credits"] = currentCredits - cred
            return True

        print "Not enough credits!"
        return


    def startBuilding(self, buildingName):
        pass


    def startDeploy(self, storage):
        self.storage = storage
        self.setMode(self.MODE_DEPLOY)