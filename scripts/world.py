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
from fife.extensions.savers import saveMapFile
from fife.extensions.soundmanager import SoundManager
from agents.hero import Hero
from agents.girl import Girl
from agents.cloud import Cloud
from agents.unit import *
from agents.beekeeper import Beekeeper
from agents.agent import create_anonymous_agents
from fife.extensions.fife_settings import Setting

from gui.huds import TacticalHUD
from combat import Trajectory

TDS = Setting(app_name="rio_de_hola")

class MapListener(fife.MapChangeListener):
    def __init__(self, map):
        fife.MapChangeListener.__init__(self)
        map.addChangeListener(self)

    def onMapChanged(self, map, changedLayers):
        return
        print "Changes on map ", map.getId()
        for layer in map.getLayers():
            print layer.getId()
            print "    ", ["%s, %x" % (i.getObject().getId(), i.getChangeInfo()) for i in layer.getChangedInstances()]

    def onLayerCreate(self, map, layer):
        pass

    def onLayerDelete(self, map, layer):
        pass

_MODE_DEFAULT, _MODE_ATTACK, _MODE_DROPSHIP = xrange(3)
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


class World(EventListenerBase):
    """
    The world!

    This class handles:
      setup of map view (cameras ...)
      loading the map
      GUI for right clicks
      handles mouse/key events which aren't handled by the GUI.
       ( by inheriting from EventlistenerBase )

    That's obviously too much, and should get factored out.
    """
    def __init__(self, engine):
        super(World, self).__init__(engine, regMouse=True, regKeys=True)
        self.engine = engine
        self.eventmanager = engine.getEventManager()
        self.model = engine.getModel()
        self.filename = ''
        self.pump_ctr = 0 # for testing purposis
        self.ctrldown = False
        self.instancemenu = None
        self.instance_to_agent = {}
        self.dynamic_widgets = {}
        self.mode = _MODE_DEFAULT
        self.tacticalHUD = TacticalHUD(self)
        self.tacticalHUD.show()

        ## Added by Jon
        self.mousePos = (100,100)   ## this is used to move the camera. Alternative method possible!
        self.factionUnits = {}      ## This will hold the units for each faction.
        self.activeUnit = None      ## Will point at the active unit "Agent" ID.
        self.activeUnitRenderer = None
        self.currentTurn = True
        self._player1 = True
        self._player2 = False
        self._objectsToDelete = list()

        self.cursorHandler = CursorHandler(self.engine.getImageManager(), self.engine.getCursor())


        ## Constants
        self._camMoveMargin = 20
        self._camMoveSpeed = 0.1
        self.light_intensity = 1
        self.light_sources = 0
        self.lightmodel = int(TDS.get("FIFE", "Lighting"))

        self.soundmanager = SoundManager(self.engine)
        self.music = None

    '''
    def show_instancemenu(self, clickpoint, instance):
        """
        Build and show a popupmenu for an instance that the player
        clicked on. The available actions are dynamically added to
        the menu (and mapped to the onXYZ functions).
        """
#               if instance.getFifeId() == self.hero.agent.getFifeId():
#                       return

        # Create the popup.
        self.build_instancemenu()
        self.instancemenu.clickpoint = clickpoint
        self.instancemenu.instance = instance

        # Add the buttons according to circumstances.
        self.instancemenu.addChild(self.dynamic_widgets['inspectButton'])

        if instance.getFifeId() == self.hero.agent.getFifeId():
            print "This is the hero."
            self.instancemenu.addChild(self.dynamic_widgets['skipTurn'])
            self.instancemenu.addChild(self.dynamic_widgets['test'])

        else:
            target_distance = self.hero.agent.getLocationRef().getLayerDistanceTo(instance.getLocationRef())
            if target_distance > 3.0:
                self.instancemenu.addChild(self.dynamic_widgets['moveButton'])
            else:
                if self.instance_to_agent.has_key(instance.getFifeId()):
                    self.instancemenu.addChild(self.dynamic_widgets['talkButton'])
                    self.instancemenu.addChild(self.dynamic_widgets['kickButton'])
        # And show it :)
        self.instancemenu.position = (clickpoint.x, clickpoint.y)
        self.instancemenu.show()

    def build_instancemenu(self):
        """
        Just loads the menu from an XML file
        and hooks the events up.
        The buttons are removed and later re-added if appropiate.
        """
        self.hide_instancemenu()
        dynamicbuttons = ('moveButton', 'talkButton', 'kickButton', 'inspectButton', 'skipTurn', 'test')
        self.instancemenu = pychan.loadXML('gui/instancemenu.xml')
        self.instancemenu.mapEvents({
                'moveButton' : self.onMoveButtonPress,
                'talkButton' : self.onTalkButtonPress,
                'kickButton' : self.onKickButtonPress,
                'inspectButton' : self.onInspectButtonPress,
                'skipTurn' : self.onSkipTurnPress,
                'test' : self.onTestPress,
        })
        for btn in dynamicbuttons:
            self.dynamic_widgets[btn] = self.instancemenu.findChild(name=btn)
        self.instancemenu.removeAllChildren()

    def hide_instancemenu(self):
        if self.instancemenu:
            self.instancemenu.hide()

    '''

    def reset(self):
        """
        Clear the agent information and reset the moving secondary camera state.
        """
        if self.music:
            self.music.stop()

        self.map, self.agentlayer = None, None
        self.cameras = {}
        # self.hero, self.girl, self.clouds, self.beekeepers = None, None, [], []
        self.cur_cam2_x, self.initial_cam2_x, self.cam2_scrolling_right = 0, 0, True
        self.target_rotation = 0
        self.instance_to_agent = {}

    def load(self, filename):
        """
        Load a xml map and setup agents and cameras.
        """

        self.filename = filename
        self.reset()
        loader = fife.MapLoader(self.engine.getModel(),
                                                        self.engine.getVFS(),
                                                        self.engine.getImageManager(),
                                                        self.engine.getRenderBackend())

        if loader.isLoadable(filename):
            self.map = loader.load(filename)

        self.initAgents()
        self.initCameras()

        #Set background color
        self.engine.getRenderBackend().setBackgroundColor(80,80,255)

        if int(TDS.get("FIFE", "PlaySounds")):
            # play track as background music
            self.music = self.soundmanager.createSoundEmitter('music/rio_de_hola.ogg')
            self.music.looping = True
            self.music.gain = 128.0
            self.music.play()

            self.waves = self.soundmanager.createSoundEmitter('sounds/waves.ogg')
            self.waves.looping = True
            self.waves.gain = 16.0
            self.waves.play()

    def initAgents(self):
        """
        Setup agents.

        For this techdemo we have a very simple 'active things on the map' model,
        which is called agents. All rio maps will have a separate layer for them.

        Note that we keep a mapping from map instances (C++ model of stuff on the map)
        to the python agents for later reference.
        """
        self.agentlayer = self.map.getLayer('TechdemoMapGroundObjectLayer')
        self.hero = HumanSquad(TDS, self.model, 'PC', self.agentlayer, self)
        self.instance_to_agent[self.hero.agent.getFifeId()] = self.hero
        self.factionUnits[self._player1] = [self.hero.agent.getFifeId()]
        self.hero.start()

        self.girl = HumanSquad(TDS, self.model, 'NPC:girl', self.agentlayer, self)
        self.instance_to_agent[self.girl.agent.getFifeId()] = self.girl
        self.factionUnits[self._player2] = [self.girl.agent.getFifeId()]
        self.girl.start()


        ## Spawn additional units:



        # Fog of War stuff
        #self.hero.agent.setVisitor(True)
        #self.hero.agent.setVisitorRadius(2)
        #self.girl.agent.setVisitor(True)
        #self.girl.agent.setVisitorRadius(1)

        self.beekeepers = create_anonymous_agents(TDS, self.model, 'beekeeper', self.agentlayer, self , Beekeeper)
        for beekeeper in self.beekeepers:
            self.instance_to_agent[beekeeper.agent.getFifeId()] = beekeeper
            self.factionUnits[self._player2].append(beekeeper.agent.getFifeId())
            beekeeper.start()

        # # Clouds are currently defunct.
        # cloudlayer = self.map.getLayer('TechdemoMapTileLayer')
        # self.clouds = create_anonymous_agents(TDS, self.model, 'Cloud', cloudlayer, Cloud, self)
        # for cloud in self.clouds:
        #     cloud.start(0.1, 0.05)


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

        for cam in self.map.getCameras():
            camera_id = cam.getId().replace(camera_prefix, '')
            self.cameras[camera_id] = cam
            cam.resetRenderers()

        ## Commented by Jon
        #self.cameras['main'].attach(self.hero.agent)

        # Floating text renderers currently only support one font.
        # ... so we set that up.
        # You'll se that for our demo we use a image font, so we have to specify the font glyphs
        # for that one.
        renderer = fife.FloatingTextRenderer.getInstance(self.cameras['main'])
        textfont = get_manager().createFont('fonts/rpgfont.png', 0, str(TDS.get("FIFE", "FontGlyphs")));
        renderer.setFont(textfont)
        renderer.activateAllLayers(self.map)
        renderer.setBackground(100, 255, 100, 165)
        renderer.setBorder(50, 255, 50)
        renderer.setEnabled(True)

        # Activate the grid renderer on all layers
        renderer = self.cameras['main'].getRenderer('GridRenderer')
        renderer.activateAllLayers(self.map)

        #Added by Jon
        rend = fife.CellSelectionRenderer.getInstance(self.cameras['main'])
        rend.setColor(1,0,0)
        rend.activateAllLayers(self.map)

        # The small camera shouldn't be cluttered by the 'humm di dums' of our hero.
        # So we disable the renderer simply by setting its font to None.
        renderer = fife.FloatingTextRenderer.getInstance(self.cameras['small'])
        renderer.setFont(None)

        # The following renderers are used for debugging.
        # Note that by default ( that is after calling View.resetRenderers or Camera.resetRenderers )
        # renderers will be handed all layers. That's handled here.
        renderer = fife.CoordinateRenderer.getInstance(self.cameras['main'])
        renderer.setFont(textfont)
        renderer.clearActiveLayers()
        renderer.addActiveLayer(self.map.getLayer(str(TDS.get("rio", "CoordinateLayerName"))))

        renderer = self.cameras['main'].getRenderer('QuadTreeRenderer')
        renderer.setEnabled(True)
        renderer.clearActiveLayers()
        if str(TDS.get("rio", "QuadTreeLayerName")):
            renderer.addActiveLayer(self.map.getLayer(str(TDS.get("rio", "QuadTreeLayerName"))))

        # If Light is enabled in settings then init the lightrenderer.
        if self.lightmodel != 0:
            renderer = fife.LightRenderer.getInstance(self.cameras['main'])
            renderer.setEnabled(True)
            renderer.clearActiveLayers()
            renderer.addActiveLayer(self.map.getLayer('TechdemoMapGroundObjectLayer'))

        # Fog of War stuff
        renderer = fife.CellRenderer.getInstance(self.cameras['main'])
        renderer.setEnabled(True)
        renderer.clearActiveLayers()
        renderer.addActiveLayer(self.map.getLayer('TechdemoMapGroundObjectLayer'))
        concimg = self.engine.getImageManager().load("misc/black_cell.png")
        maskimg = self.engine.getImageManager().load("misc/mask_cell.png")
        renderer.setConcealImage(concimg)
        renderer.setMaskImage(maskimg)
        renderer.setFogOfWarLayer(self.map.getLayer('TechdemoMapGroundObjectLayer'))

        #disable FoW by default.  Users can turn it on with the 'f' key.
        renderer.setEnabledFogOfWar(False)

        #renderer.setEnabledBlocking(True)

        # Set up the second camera
        # NOTE: We need to explicitly call setLocation, there's a bit of a messup in the Camera code.
        '''
        girl = self.instance_to_agent[self.factionUnits[self._player2][0]]
        self.cameras['small'].setLocation(girl.agent.getLocation())
        self.cameras['small'].attach(girl.agent)
        '''
        ## Warning! if we delete an instance that is being followed the program crashes!

        self.target_rotation = self.cameras['main'].getRotation()


    def save(self, filename):
        saveMapFile(filename, self.engine, self.map)

    def getInstancesAt(self, clickpoint):
        """
        Query the main camera for instances on our active(agent) layer.
        """
        return self.cameras['main'].getMatchingInstances(clickpoint, self.agentlayer)

    def getLocationAt(self, clickpoint):
        """
        Query the main camera for the Map location (on the agent layer)
        that a screen point refers to.
        """
        target_mapcoord = self.cameras['main'].toMapCoordinates(clickpoint, False)
        target_mapcoord.z = 0
        location = fife.Location(self.agentlayer)
        location.setMapCoordinates(target_mapcoord)
        return location

    def keyPressed(self, evt):
        keyval = evt.getKey().getValue()
        keystr = evt.getKey().getAsString().lower()
        if keystr == 't':
            r = self.cameras['main'].getRenderer('GridRenderer')
            r.setEnabled(not r.isEnabled())
        elif keystr == 'c':
            r = self.cameras['main'].getRenderer('CoordinateRenderer')
            r.setEnabled(not r.isEnabled())
        elif keystr == 's':
            c = self.cameras['small']
            c.setEnabled(not c.isEnabled())
        elif keystr == 'r':
            self.model.deleteMaps()
            self.load(self.filename)
        elif keystr == 'f':
            renderer = fife.CellRenderer.getInstance(self.cameras['main'])
            renderer.setEnabledFogOfWar(not renderer.isEnabledFogOfWar())
            self.cameras['main'].refresh()
        elif keystr == 'o':
            self.target_rotation = (self.target_rotation + 90) % 360
        elif keystr == '2':
            self.lightIntensity(0.1)
        elif keystr == '1':
            self.lightIntensity(-0.1)
        elif keystr == '5':
            self.lightSourceIntensity(25)
        elif keystr == 'n':
            self.nextTurn()
        elif keystr == 'a':
            self.onAttackButtonPressed()
        elif keystr == '4':
            self.lightSourceIntensity(-25)
        elif keystr == '0' or keystr == fife.Key.NUM_0:
            if self.ctrldown:
                self.cameras['main'].setZoom(1.0)
        elif keyval in (fife.Key.LEFT_CONTROL, fife.Key.RIGHT_CONTROL):
            self.ctrldown = True

    def onAttackButtonPressed(self):
        self.setMode(_MODE_ATTACK)

    def keyReleased(self, evt):
        keyval = evt.getKey().getValue()
        if keyval in (fife.Key.LEFT_CONTROL, fife.Key.RIGHT_CONTROL):
            self.ctrldown = False

    def mouseWheelMovedUp(self, evt):
        if self.ctrldown:
            self.cameras['main'].setZoom(self.cameras['main'].getZoom() * 1.05)

    def mouseWheelMovedDown(self, evt):
        if self.ctrldown:
            self.cameras['main'].setZoom(self.cameras['main'].getZoom() / 1.05)

    def changeRotation(self):
        """
        Smoothly change the main cameras rotation until
        the current target rotation is reached.
        """
        currot = self.cameras['main'].getRotation()
        if self.target_rotation != currot:
            self.cameras['main'].setRotation((currot + 5) % 360)


    def clickDefault(self, clickpoint):
        # self.hide_instancemenu()

        instances = self.getInstancesAt(clickpoint)
        print "selected instances on agent layer: ", [i.getObject().getId() for i in instances]
        print "Found " , instances.__len__(), "instances"

        if instances:
            # self.activeUnit = None
            print "Current turn:" , self.currentTurn
            for instance in instances:
                id = instance.getFifeId()
                print "Instance: ", id
                print "Is it in: ", self.factionUnits[self.currentTurn]
                if id in self.factionUnits[self.currentTurn]:
                    print "Instance: " , id, " is owned by this player!"
                    #self.activeUnit = id
                    self.selectUnit(id)
        if self.activeUnit:
            self.instance_to_agent[self.activeUnit].run(self.getLocationAt(clickpoint))

        # ## Test
        # clickLocation = self.getLocationAt(clickpoint)
        # unit = self.instance_to_agent[self.activeUnit]
        # unitLocation = unit.agent.getLocation()
        #
        # print "Clicked Location (Tile): " , clickLocation.getLayerCoordinates()
        # print "Clicked Location (Map):" , clickLocation.getMapCoordinates()
        # print "Unit Location:" , unitLocation.getLayerCoordinates()
        # print "Unit Location (Map):" , unitLocation.getMapCoordinates()
        # if clickLocation.getLayerCoordinates() == unitLocation.getLayerCoordinates():
        #     print "They are in the same location!"


    def getUnitsInTile(self, tileLocation):
        '''
        Returns a list of unit IDs that are located in the specified tile position
        :param tileLocation: Location object.
        :return: List of IDs
        '''

        tilePos = tileLocation.getLayerCoordinates()
        unitIDs = []
        for id in self.instance_to_agent.keys():
            unitLocation = self.instance_to_agent[id].agent.getLocation().getLayerCoordinates()
            if tilePos == unitLocation:
                unitIDs.append(id)

        print "Found ", unitIDs.__len__(), " units on this tile."
        return unitIDs

    def clickAttack(self, clickpoint):
        '''
        Handles the click action when attack is selected.
        :return:
        '''
        if not self.activeUnit:
            return

        clickLocation = self.getLocationAt(clickpoint)
        trajectory = Trajectory(self.instance_to_agent[self.activeUnit], self.cameras['main'], self,0)
        # print "Is is reachable?"
        if trajectory.isInRange(clickLocation):

        # print "Calculating Clear path:"
            if trajectory.hasClearPath(clickLocation):
                self.instance_to_agent[self.activeUnit].attack(clickLocation)


    def mousePressed(self, evt):
        if evt.isConsumedByWidgets():
            return

        clickpoint = fife.ScreenPoint(evt.getX(), evt.getY())
        if (evt.getButton() == fife.MouseEvent.LEFT):
            if self.mode == _MODE_DEFAULT:
                self.clickDefault(clickpoint)
            elif self.mode == _MODE_ATTACK:
                self.clickAttack(clickpoint)

        if (evt.getButton() == fife.MouseEvent.RIGHT):
            self.setMode(_MODE_DEFAULT)
            instances = self.getInstancesAt(clickpoint)
            print "selected instances on agent layer: ", [i.getObject().getId() for i in instances]
            if instances:
                print "Instance menu should've been shown "
                # self.show_instancemenu(clickpoint, instances[0])
            else:
                self.selectUnit(None)

    def mouseMoved(self, evt):

        self.mousePos = (evt.getX(), evt.getY())
        # renderer = fife.InstanceRenderer.getInstance(self.cameras['main'])
        # renderer.removeAllOutlines()

        # pt = fife.ScreenPoint(evt.getX(), evt.getY())
        # instances = self.getInstancesAt(pt);
        # for i in instances:
        #     if i.getObject().getId() in ('girl', 'beekeeper'):
        #         renderer.addOutlined(i, 173, 255, 47, 2)


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

        ## Not working properly: Freezing program and PC!!!
        # mainCamera = self.cameras['main']
        # center = fife.Point3D(1024/2, 768/2, 0)
        # vector = fife.Point3D(-1,0,0)
        # displaced = center + vector
        # nextPoint = mainCamera.toMapCoordinates(displaced)
        # nextLocation = mainCamera.getLocation()
        # nextLocation.setMapCoordinates(nextPoint)
        # mainCamera.setLocation(nextLocation)

        #print dir(currentPos)


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

    def onConsoleCommand(self, command):
        result = ''
        try:
            result = str(eval(command))
        except Exception, e:
            result = str(e)
        return result

    # Callbacks from the popupmenu
    def onMoveButtonPress(self):
        self.hide_instancemenu()
        self.hero.run(self.instancemenu.instance.getLocationRef())

    def onTalkButtonPress(self):
        self.hide_instancemenu()
        instance = self.instancemenu.instance
        self.hero.talk(instance.getLocationRef())
        if instance.getObject().getId() == 'beekeeper':
            beekeeperTexts = TDS.get("rio", "beekeeperTexts")
            instance.say(random.choice(beekeeperTexts), 5000)
        if instance.getObject().getId() == 'girl':
            girlTexts = TDS.get("rio", "girlTexts")
            instance.say(random.choice(girlTexts), 5000)

    def onKickButtonPress(self):
        self.hide_instancemenu()
        self.hero.kick(self.instancemenu.instance.getLocationRef())
        self.instancemenu.instance.say('Hey!', 1000)

    def onInspectButtonPress(self):
        self.hide_instancemenu()
        inst = self.instancemenu.instance
        saytext = ['Engine told me that this instance has']
        if inst.getId():
            saytext.append(' name %s,' % inst.getId())
        saytext.append(' ID %s and' % inst.getFifeId())
        saytext.append(' object name %s' % inst.getObject().getId())
        self.hero.agent.say('\n'.join(saytext), 3500)

    def onSkipTurnPress(self):
        print "Skipping turn!"
        self.nextTurn()

    def pump(self):
        """
        Called every frame.
        """

        # self.collectGarbage()

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


    def handleCursor(self):
        '''
        Changes the cursor according to the mode.
        :return:
        '''
        if self.mode == _MODE_ATTACK:
            if not self.activeUnit:
                return

            mousepoint = fife.ScreenPoint(self.mousePos[0], self.mousePos[1])
            mouseLocation = self.getLocationAt(mousepoint)
            trajectory = Trajectory(self.instance_to_agent[self.activeUnit], self.cameras['main'], self,0)
            # print "Is is reachable?"
            self.cursorHandler.setCursor(_CUR_CANNOT)
            if trajectory.isInRange(mouseLocation):
                if trajectory.hasClearPath(mouseLocation):
                    # print "Changing cursor"
                    self.cursorHandler.setCursor(_CUR_ATTACK)

        else:
            self.cursorHandler.setCursor(_CUR_DEFAULT)



    def resetAPs(self):
        '''
        Resets the AP points of all the units to its maximum.
        '''
        for unitID in self.factionUnits[self.currentTurn]:
            print "Reseting: ", unitID
            unit = self.instance_to_agent[unitID]
            unit.resetAP()

    def nextTurn(self):
        '''
        Skips to the next turn
        '''
        self.currentTurn = not self.currentTurn
        self.selectUnit(None)
        self.resetAPs()
        self.setMode(_MODE_DEFAULT)
        ## TO-DO: add a message stating who's turn it is.
        # print self.instance_to_agent
        # for key in self.instance_to_agent.keys():
        #     instance = self.instance_to_agent[key]
        #     instance.runTurn()

    def getInstance(self, id):
        '''
        :param id: FIFEID of the agent you want to obtain
        :return: Instance
        '''
        ids = self.agentlayer.getInstances()
        instance = [i for i in ids if i.getFifeId() == id]
        if instance:
            return instance[0]



    def selectUnit(self, id):

        ## Create an InstanceRenderer if not existing
        if not self.activeUnitRenderer:
            self.activeUnitRenderer = fife.InstanceRenderer.getInstance(self.cameras['main'])
            #renderer.removeAllOutlines()

        ## Clear previously selected unit
        if self.activeUnit != id:
            if self.activeUnit:
                self.activeUnitRenderer.removeOutlined(self.getInstance(self.activeUnit))

        self.activeUnit = id
        if id:
            self.activeUnitRenderer.addOutlined(self.getInstance(id), 173, 255, 47, 2)

             ## Show it on the mini-camera:
            print "Trying to show in the mini-camera"
            unit = self.instance_to_agent[id]
            self.cameras['small'].setLocation(unit.agent.getLocation())
            self.cameras['small'].attach(unit.agent)
            self.cameras['small'].setEnabled(True)

        else:
            self.cameras['small'].detach()
            self.cameras['small'].setEnabled(False)

    def setMode(self, mode):
        '''
        Sets the current runtime tactical mode.
        :param mode: _MODE_DEFAULT, _MODE_ATTACK, _MODE_DROPSHIP
        :return:
        '''

        self.mode = mode
        # Change cursor type
        # dictionary containing {mode:cursor}
        # cursor = self.engine.getCursor()
        # cursorfile = self.settings.get("rio", "CursorAttack")
        # cursorImage = cursor.getImage()

    def applyDamage(self, location, damage):
        '''
        Deals damage to a specific location (and all the units within).
        :param location: Place where the damage is applied in the map.
        :param damage: Ammount of damage dealt
        :return:
        '''
        targetIDs = self.getUnitsInTile(location)
        for unitID in targetIDs:
            self.instance_to_agent[unitID].getDamage(damage)
            print "Unit ", unitID, "recieved damage!"

    def unitDied(self, unitID):
        '''
        Process the destruction of a unit
        :param unitID: ID of the destroyed unit
        :return:
        '''


        if unitID in self.instance_to_agent.keys():
            obj = self.instance_to_agent[unitID]
            self.instance_to_agent.__delitem__(unitID)
            self.agentlayer.deleteInstance(obj.instance)
        for player in range(2):
            if unitID in self.factionUnits[player]:
                self.factionUnits[player].remove(unitID)
        else:
            print "Could not delete instance: " , unitID

    '''
    def collectGarbage(self):
        """
		This should be called once a frame.  It removes the object from the scene.
		"""
        for id in self._objectsToDelete:
            self.removeObjectFromScene(id)

        self._objectstodelete = list()

    def removeObjectFromScene(self, id):
        """
		You would not normally call this function directly.  You should probably
		call queueObjectForRemoval().

		This function releases any memory allocated for the object by deleting
		the FIFE instance.

		@param obj: The object to delete
		"""
        obj = self.instance_to_agent[id]
        self._layer.deleteInstance(obj.instance)
    '''