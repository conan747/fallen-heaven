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
from agents.hero import Hero
from agents.girl import Girl
from agents.cloud import Cloud
from agents.unit import *
from fife.extensions.fife_settings import Setting

from gui.huds import TacticalHUD
from combat import Trajectory
from scripts.tactic_scene import TacticScene

TDS = Setting(app_name="rio_de_hola")


_MODE_DEFAULT, _MODE_ATTACK, _MODE_DROPSHIP = xrange(3)


class WorldListener(fife.IKeyListener, fife.IMouseListener):
    """
	Main game listener.  Listens for Mouse and Keyboard events.

	This class also has the ability to attach and detach itself from
	the event manager in cases where you do not want input processed (i.e. when
	the main menu is visible).  It is NOT attached by default.
	"""

    ## TODO: Handle selection by cell not by image. (In order to select ocluded instances.) What about the case of buildings?

    def __init__(self, world):
        self._engine = world.engine
        self._world = world
        self._settings = world.settings
        self._eventmanager = self._engine.getEventManager()

        fife.IMouseListener.__init__(self)
        fife.IKeyListener.__init__(self)

        self.ctrldown = False

        self._attached = False

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


    def clickDefault(self, clickpoint):
        # self.hide_instancemenu()

        instances = self._world.getInstancesAt(clickpoint)
        print "selected instances on agent layer: ", [i.getObject().getId() for i in instances]
        print "Found " , instances.__len__(), "instances"

        if instances:
            # self.activeUnit = None
            for instance in instances:
                id = instance.getFifeId()
                print "Instance: ", id
                if id in self._world.scene.instance_to_agent.keys():
                    self._world.selectUnit(id)
        if self._world.activeUnit:
            self._world.scene.instance_to_agent[self._world.activeUnit].teleport(self._world.getLocationAt(clickpoint))


    def mousePressed(self, evt):
        if evt.isConsumedByWidgets():
            return

        clickpoint = fife.ScreenPoint(evt.getX(), evt.getY())
        if (evt.getButton() == fife.MouseEvent.LEFT):
            if self._world.mode == _MODE_DEFAULT:
                self.clickDefault(clickpoint)
            elif self._world.mode == _MODE_ATTACK:
                self.clickAttack(clickpoint)

        if (evt.getButton() == fife.MouseEvent.RIGHT):
            self._world.setMode(_MODE_DEFAULT)
            instances = self._world.getInstancesAt(clickpoint)
            print "selected instances on agent layer: ", [i.getObject().getId() for i in instances]
            if instances:
                print "Instance menu should've been shown "
                # self.show_instancemenu(clickpoint, instances[0])
            else:
                self._world.selectUnit(None)


    def mouseReleased(self, event):
        pass

    def mouseMoved(self, evt):

        self._world.mousePos = (evt.getX(), evt.getY())


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
        # if keyval == fife.Key.ESCAPE:
        #     self.detach()
        #     self._world.guicontroller.showMainMenu()
        #     event.consume()
        # self._world.keystate.updateKey(keyval, True)


    def keyReleased(self, evt):
        keyval = evt.getKey().getValue()
        if keyval in (fife.Key.LEFT_CONTROL, fife.Key.RIGHT_CONTROL):
            self.ctrldown = False


_CUR_DEFAULT, _CUR_ATTACK, _CUR_CANNOT = xrange(3)


class CursorHandler(object):
    '''
    Handles the information for the cursor.
    '''
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



        self.cursorDict = {_CUR_DEFAULT: normalCursor,
                           _CUR_ATTACK: cursorAttack,
                          _CUR_CANNOT: cannot}

        self.setCursor(_CUR_DEFAULT)

    def setCursor(self, cursorId):
        cursorImg = self.cursorDict[cursorId]
        self._cursor.set(cursorImg)



class World(object):
    """
    The world!

    This class handles:
      setup of map view (cameras ...)
      loading the scene

    That's obviously too much, and should get factored out.
    """
    def __init__(self, engine, settings):
        # super(World, self).__init__(engine, regMouse=True, regKeys=True)
        self.engine = engine
        self.eventmanager = engine.getEventManager()
        self.model = engine.getModel()
        self.filename = ''
        self.pump_ctr = 0 # for testing purposis
        self.ctrldown = False
        self.instancemenu = None
        self.dynamic_widgets = {}

        self.settings = settings


        ## Added by Jon
        self.mousePos = (100,100)   ## this is used to move the camera. Alternative method possible!
        # self.factionUnits = {}      ## This will hold the units for each faction.
        self.activeUnit = None      ## Will point at the active unit "Agent" ID.
        self.activeUnitRenderer = None
        # self.currentTurn = True
        # self._player1 = True
        # self._player2 = False
        # self._objectsToDelete = list()
        self.mode = _MODE_DEFAULT


        self.cursorHandler = CursorHandler(self.engine.getImageManager(), self.engine.getCursor())


        ## Constants
        self._camMoveMargin = 20
        self._camMoveSpeed = 0.1
        self.light_intensity = 1
        self.light_sources = 0
        self.lightmodel = int(TDS.get("FIFE", "Lighting"))

        self.soundmanager = SoundManager(self.engine)
        self.music = None


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
        self.scene.load(filename)

        if int(self.settings.get("FIFE", "PlaySounds")):
            # play track as background music
            self.music = self.soundmanager.createSoundEmitter('music/rio_de_hola.ogg')
            self.music.looping = True
            self.music.gain = 128.0
            self.music.play()

            self.waves = self.soundmanager.createSoundEmitter('sounds/waves.ogg')
            self.waves.looping = True
            self.waves.gain = 16.0
            self.waves.play()


        self.listener.attach()
        # self._music = self._soundmanager.createSoundEmitter("music/waynesmind2.ogg")
        # self._music.callback = self.musicHasFinished
        # self._music.looping = True
        # self._soundmanager.playClip(self._music)

    def initCameras(self):
        """
        Before we can actually see something on screen we have to specify the render setup.
        This is done through Camera objects which offer a viewport on the map.

        For this techdemo two cameras are used. One follows the hero(!) via 'attach'
        the other one scrolls around a bit (see the pump function).
        """
        camera_prefix = self.filename.rpartition('.')[0] # Remove file extension
        camera_prefix = camera_prefix.rpartition('/')[2] # Remove path
        camera_prefix += '_'

        for cam in self.scene.map.getCameras():
            camera_id = cam.getId().replace(camera_prefix, '')
            self.cameras[camera_id] = cam
            cam.resetRenderers()

        # Floating text renderers currently only support one font.
        # ... so we set that up.
        # You'll se that for our demo we use a image font, so we have to specify the font glyphs
        # for that one.
        renderer = fife.FloatingTextRenderer.getInstance(self.cameras['main'])
        textfont = get_manager().createFont('fonts/rpgfont.png', 0, str(TDS.get("FIFE", "FontGlyphs")));
        renderer.setFont(textfont)
        renderer.activateAllLayers(self.scene.map)
        renderer.setBackground(100, 255, 100, 165)
        renderer.setBorder(50, 255, 50)
        renderer.setEnabled(True)

        # Activate the grid renderer on all layers
        renderer = self.cameras['main'].getRenderer('GridRenderer')
        renderer.activateAllLayers(self.scene.map)

        #Added by Jon
        rend = fife.CellSelectionRenderer.getInstance(self.cameras['main'])
        rend.setColor(1,0,0)
        rend.activateAllLayers(self.scene.map)

        # The following renderers are used for debugging.
        # Note that by default ( that is after calling View.resetRenderers or Camera.resetRenderers )
        # renderers will be handed all layers. That's handled here.
        renderer = fife.CoordinateRenderer.getInstance(self.cameras['main'])
        renderer.setFont(textfont)
        renderer.clearActiveLayers()
        renderer.addActiveLayer(self.scene.map.getLayer(str(TDS.get("rio", "CoordinateLayerName"))))

        renderer = self.cameras['main'].getRenderer('QuadTreeRenderer')
        renderer.setEnabled(True)
        renderer.clearActiveLayers()
        if str(TDS.get("rio", "QuadTreeLayerName")):
            renderer.addActiveLayer(self.scene.map.getLayer(str(TDS.get("rio", "QuadTreeLayerName"))))

        # If Light is enabled in settings then init the lightrenderer.
        if self.lightmodel != 0:
            renderer = fife.LightRenderer.getInstance(self.cameras['main'])
            renderer.setEnabled(True)
            renderer.clearActiveLayers()
            renderer.addActiveLayer(self.scene.map.getLayer('TechdemoMapGroundObjectLayer'))

        # Fog of War stuff
        renderer = fife.CellRenderer.getInstance(self.cameras['main'])
        renderer.setEnabled(True)
        renderer.clearActiveLayers()
        renderer.addActiveLayer(self.scene.map.getLayer('TechdemoMapGroundObjectLayer'))
        concimg = self.engine.getImageManager().load("misc/black_cell.png")
        maskimg = self.engine.getImageManager().load("misc/mask_cell.png")
        renderer.setConcealImage(concimg)
        renderer.setMaskImage(maskimg)
        renderer.setFogOfWarLayer(self.scene.map.getLayer('TechdemoMapGroundObjectLayer'))

        #disable FoW by default.  Users can turn it on with the 'f' key.
        renderer.setEnabledFogOfWar(False)

        #renderer.setEnabledBlocking(True)
        self.target_rotation = self.cameras['main'].getRotation()


    def getInstancesAt(self, clickpoint):
        """
        Query the main camera for instances on our active(agent) layer.
        """
        return self.cameras['main'].getMatchingInstances(clickpoint, self.scene.agentLayer)

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
            self.activeUnitRenderer = fife.InstanceRenderer.getInstance(self.cameras['main'])
            #renderer.removeAllOutlines()

        ## Clear previously selected unit
        if self.activeUnit != id:
            if self.activeUnit:
                self.activeUnitRenderer.removeOutlined(self.scene.getInstance(self.activeUnit))
                ### !!!! CHekc if we can improve this!

        self.activeUnit = id
        if id:
            self.activeUnitRenderer.addOutlined(self.scene.getInstance(id), 173, 255, 47, 2)

            ## Get rid of all this because we don't have it on the original game.
            ## Show it on the mini-camera:
            print "Trying to show in the mini-camera"
            unit = self.scene.instance_to_agent[id]
            self.cameras['small'].setLocation(unit.agent.getLocation())
            self.cameras['small'].attach(unit.agent)
            self.cameras['small'].setEnabled(True)

        else:
            self.cameras['small'].detach()
            self.cameras['small'].setEnabled(False)

    def changeRotation(self):
        """
        Smoothly change the main cameras rotation until
        the current target rotation is reached.
        """
        currot = self.cameras['main'].getRotation()
        if self.target_rotation != currot:
            self.cameras['main'].setRotation((currot + 5) % 360)



    def moveCamera(self, speedVector):
        ''' Checks if the mouse is on the edge of the screen and moves the camera accordingly'''

        mainCamera = self.cameras['main']
        #speedVector = (-0.5,0)
        angle = mainCamera.getRotation()
        currentLocation = mainCamera.getLocation()
        # print "Close to the edge!"
        vector = fife.DoublePoint3D(speedVector[0] * math.cos(angle) - speedVector[1] * math.sin(angle),
                                    speedVector[0] * math.sin(angle) + speedVector[1] * math.cos(angle),0)
        currentPoint = currentLocation.getMapCoordinates()
        newPoint = currentPoint + vector
        currentLocation.setMapCoordinates(newPoint)
        mainCamera.setLocation(currentLocation)


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
            self._nextTurnWindow = pychan.loadXML('gui/dialogs/next_turn.xml')
            self._nextTurnWindow.mapEvents({ 'closeButton' : self._nextTurnWindow.hide })

        text = "This is the turn of"
        if not self.scene.currentTurn:
            text += " Player 1"
        else:
            text += " Player 2"
        self._nextTurnWindow.distributeData({ 'text' : text })
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
            speedVector = (-self._camMoveSpeed,0)
            self.moveCamera(speedVector)

        if self.mousePos[0] > (engineSettings.getScreenWidth()-self._camMoveMargin):
            speedVector = (self._camMoveSpeed,0)
            self.moveCamera(speedVector)

        if self.mousePos[1] < self._camMoveMargin:
            speedVector = (0,-self._camMoveSpeed)
            self.moveCamera(speedVector)

        if self.mousePos[1] > (engineSettings.getScreenHeight()-self._camMoveMargin):
            speedVector = (0,self._camMoveSpeed)
            self.moveCamera(speedVector)

        self.changeRotation()
        self.pump_ctr += 1

        ## handle mouse:
        self.handleCursor()

        self.scene.pump()

        # print "End pumping world"
