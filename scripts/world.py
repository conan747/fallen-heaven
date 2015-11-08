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
from scripts.tactic_scene import TacticScene
from gui.dialogs import InfoDialog
from view import View

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


        if self._world.scene.factionUnits:
            if id in self._world.scene.factionUnits[self._world.scene.currentTurn]:
                print "Instance: " , id, " is owned by this player!"
                self._world.selectUnit(id)
            else:
                return

        if not self.unitManager:
            self.unitManager = self._world.scene.unitManager

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
            self.unitManager = self._world.scene.unitManager

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
            self.unitManager = self._world.scene.unitManager

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
            self.unitManager = self._world.scene.unitManager

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
            self._world.scene.addBuilding(self._world.construction)
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
                    self._cellSelectionRenderer.activateAllLayers(self._world.scene.map)

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
    #             self._world.scene.player.walk(self._world.scene.getLocationAt(clickpoint))
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

    This class handles:
      setup of map view (cameras ...)
      loading the scene
    """

    MODE_DEFAULT, MODE_ATTACK, MODE_DROPSHIP, MODE_DEPLOY, MODE_BUILD, MODE_RECYCLE, MODE_GET_IN = xrange(7)


    def __init__(self, universe, planet):
        # super(World, self).__init__(engine, regMouse=True, regKeys=True)
        self.universe = universe
        self.engine = universe._engine
        self.eventmanager = self.engine.getEventManager()
        self.model = self.engine.getModel()
        self.filename = ''
        self.pump_ctr = 0 # for testing purposis
        self.ctrldown = False
        self.instancemenu = None
        self.dynamic_widgets = {}
        self.faction = universe.faction
        self.planet = planet
        self.attackType = None
        self.scene=None
        self.unitManager = None

        self.settings = universe._settings


        ## Added by Jon
        self.mousePos = (100,100)   ## this is used to move the camera. Alternative method possible!
        # self.factionUnits = {}      ## This will hold the units for each faction.
        self.activeUnit = None      ## Will point at the active unit "Agent" ID.
        self.activeUnitRenderer = None
        # self.currentTurn = True
        # self._player1 = True
        # self._player2 = False
        # self._objectsToDelete = list()
        self.mode = self.MODE_DEFAULT
        self.storage = None # Points at the storage object in Deploy mode.
        self.deploying = None

        self.view = View(self, self.engine)

        self.cursorHandler = CursorHandler(self.engine.getImageManager(), self.engine.getCursor())


        ## Constants
        self._camMoveMargin = 20
        self._camMoveSpeed = 0.2
        self.light_intensity = 1
        self.light_sources = 0
        self.lightmodel = int(TDS.get("FIFE", "Lighting"))

        self.sound = self.universe.sound
        self.music = None

        self.busy = False

        ## There can only be one world -> assign unitLoader to this world.
        self.universe.unitLoader.setWorld(self)

    def getActiveAgent(self):
        '''
        Returns the active agent.
        :return: Agent
        '''
        if self.activeUnit:
            if not self.unitManager:
                self.unitManager = self.scene.unitManager

            return self.unitManager.getAgent(self.activeUnit)


    def moveCamera(self, speedVector):
        self.view.moveCamera(speedVector)

    def reset(self):
        """
        Clear the agent information and reset the moving secondary camera state.
        """
        if self.music:
            self.music.stop()

        # self.scene.map, self.agentLayer = None, None
        self.cameras = {}
        # self.hero, self.girl, self.clouds, self.beekeepers = None, None, [], []
        self.cur_cam2_x, self.initial_cam2_x, self.cam2_scrolling_right = 0, 0, True
        self.target_rotation = 0
        # self.instance_to_agent = {}

    def load(self, filename):
        """
        Load a xml map and setup agents and cameras.
        """
        self.reset()
        self.filename = filename
        self.scene.load(filename)

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


        self.listener.attach()
        # self._music = self._soundmanager.createSoundEmitter("music/waynesmind2.ogg")
        # self._music.callback = self.musicHasFinished
        # self._music.looping = True
        # self._soundmanager.playClip(self._music)


    def initView(self, map):
        self.view.load(map)
        self.cameras = self.view.cameras


    def getInstancesAt(self, arg):
        """
        Query the main camera for instances on our active(agent) layer.
        :param arg: Location or Point3D.
        :return: List of instance IDs.
        """
        if isinstance(arg, fife.Point3D) or isinstance(arg, fife.ScreenPoint):
            return self.cameras['main'].getMatchingInstances(arg, self.scene.agentLayer)
        elif isinstance(arg, fife.Location):
            return self.scene.agentLayer.getInstancesAt(arg)


    # def getInstancesAt(self, clickpoint):
    #     """
    #     Query the main camera for instances on our active(agent) layer.
    #     """
    #     if isinstance(clickpoint)
    #     instances = self.cameras['main'].getMatchingInstances(clickpoint, self.scene.agentLayer)
    #
    #     if not instances:
    #         location = self.getLocationAt(clickpoint)
    #         return self.cameras['main'].getMatchingInstances(location, False)
    #
    #     return instances

    def getLocationAt(self, clickpoint):
        """
        Query the main camera for the Map location (on the agent layer)
        that a screen point refers to.
        """
        target_mapcoord = self.cameras['main'].toMapCoordinates(clickpoint, False)
        target_mapcoord.z = 0
        location = fife.Location(self.scene.agentLayer)
        location.setMapCoordinates(target_mapcoord)
        return location



    def selectUnit(self, id):

        ## Create an InstanceRenderer if not existing
        if not self.activeUnitRenderer:
            self.activeUnitRenderer = self.view.renderer["InstanceRenderer"]

        ## Clear previously selected unit
        if self.activeUnit != id:
            if self.activeUnit:
                self.activeUnitRenderer.removeOutlined(self.scene.getInstance(self.activeUnit).instance)

        self.activeUnit = id
        if id:
            self.activeUnitRenderer.addOutlined(self.scene.getInstance(id).instance, 173, 255, 47, 2)

        # Update UI:
        self.HUD.updateUI()

    def changeRotation(self):
        """
        Smoothly change the main cameras rotation until
        the current target rotation is reached.
        """
        currot = self.cameras['main'].getRotation()
        if self.target_rotation != currot:
            self.cameras['main'].setRotation((currot + 5) % 360)


    def lightIntensity(self, value):
        if self.light_intensity+value <= 1 and self.light_intensity+value >= 0:
            self.light_intensity = self.light_intensity + value

            if self.lightmodel == 1:
                self.cameras['main'].setLightingColor(self.light_intensity, self.light_intensity, self.light_intensity)

    def lightSourceIntensity(self, value):
        if self.light_sources+value <= 255 and self.light_sources+value >= 0:
            self.light_sources = self.light_sources+value
            renderer = fife.LightRenderer.getInstance(self.cameras['main'])

            renderer.removeAll("beekeeper_simple_light")
            renderer.removeAll("hero_simple_light")
            renderer.removeAll("girl_simple_light")

            if self.lightmodel == 1:
                node = fife.RendererNode(self.hero.agent)
                renderer.addSimpleLight("hero_simple_light", node, self.light_sources, 64, 32, 1, 1, 255, 255, 255)

                node = fife.RendererNode(self.girl.agent)
                renderer.addSimpleLight("girl_simple_light", node, self.light_sources, 64, 32, 1, 1, 255, 255, 255)

                for beekeeper in self.beekeepers:
                    node = fife.RendererNode(beekeeper.agent)
                    renderer.addSimpleLight("beekeeper_simple_light", node, self.light_sources, 120, 32, 1, 1, 255, 255, 255)


    def onSkipTurnPress(self):
        print "Skipping turn!"

        if not self._nextTurnWindow:
            self._nextTurnWindow = InfoDialog(title="Next turn")


        text = "This is the turn of"
        if not self.scene.currentTurn:
            text += " Player 1"
        else:
            text += " Player 2"
        self._nextTurnWindow.setText(text)
        self._nextTurnWindow.show()

        self.scene.nextTurn()

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


        self.scene.pump()

        # print "End pumping world"


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
        if self.mode == self.MODE_ATTACK:
            if not self.activeUnit:
                return

            mousepoint = fife.ScreenPoint(self.mousePos[0], self.mousePos[1])
            mouseLocation = self.getLocationAt(mousepoint)

            trajectory = Trajectory( self.getActiveAgent(), self,0)
            # print "Is is reachable?"
            if trajectory.hasClearPath(mouseLocation, display=True) and trajectory.isInRange(mouseLocation) :
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