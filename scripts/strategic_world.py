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
from agents.building import *
from fife.extensions.fife_settings import Setting
from world import *

from gui.huds import StrategicHUD
from combat import Trajectory
from scripts.strategic_scene import StrategicScene

TDS = Setting(app_name="rio_de_hola")
_MODE_DEFAULT, _MODE_BUILD = xrange(2)


class StrategicListener(WorldListener):
    """
    Main game listener.  Listens for Mouse and Keyboard events.

    This class also has the ability to attach and detach itself from
    the event manager in cases where you do not want input processed (i.e. when
    the main menu is visible).  It is NOT attached by default.
    """

    def __init__(self, world):

        super(StrategicListener, self).__init__(world)
        self._cellSelectionRenderer = None


    def clickDefault(self, clickpoint):
        # self.hide_instancemenu()

        instances = self._world.getInstancesAt(clickpoint)
        print "selected instances on agent layer: ", [i.getObject().getId() for i in instances]
        print "Found " , instances.__len__(), "instances"

        if instances:
            for instance in instances:
                id = instance.getFifeId()
                print "Instance: ", id
                if id in self._world.scene.instance_to_agent.keys():
                    self._world.selectUnit(id)
                    # If it is a Building, then open the menu.
                    agent = self._world.scene.instance_to_agent[id]
                    # print "Namespace:" , instance.nameSpace
                    print "Namespace: " , agent.nameSpace
                    if agent.nameSpace == "Building":
                        self._world.HUD.updateUI()
                        self._world.HUD.structureWidget.show()
                    else:
                        self._world.HUD.structureWidget.hide()
        if self._world.activeUnit:
            self._world.scene.instance_to_agent[self._world.activeUnit].teleport(self._world.getLocationAt(clickpoint))


    def clickBuild(self, clickpoint):
        '''
        Locate the building at clickpoint.
        '''
        # We don't need to do anything since the instance should be here already.
        location = self._world.getLocationAt(clickpoint)
        construction = self._world.construction
        print "Namespace: " , construction.nameSpace
        if construction.teleport(location):
            self._world.scene.addBuilding(self._world.construction)
            self._world.construction = None
            self._world.cursorHandler.setCursor(_CUR_DEFAULT)
            self._world.setMode(_MODE_DEFAULT)
            self._world.stopBuilding()
            self._world.HUD.buildingWidget.hide()
        ## TODO: If we are building a wall then don't close the builder widget.


    def mousePressed(self, evt):
        if evt.isConsumedByWidgets():
            return

        clickpoint = fife.ScreenPoint(evt.getX(), evt.getY())
        if (evt.getButton() == fife.MouseEvent.LEFT):
            if self._world.mode == _MODE_DEFAULT:
                self.clickDefault(clickpoint)
            elif self._world.mode == _MODE_BUILD:
                self.clickBuild(clickpoint)

        if (evt.getButton() == fife.MouseEvent.RIGHT):
            if self._world.mode == _MODE_BUILD:
                self._world.stopBuilding()

            else:
                self._world.selectUnit(None)

            self._world.HUD.closeExtraWindows()


    def mouseMoved(self, evt):

        self._world.mousePos = (evt.getX(), evt.getY())

        if self._world.mode == _MODE_DEFAULT:
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

        elif self._world.mode == _MODE_BUILD:
            construction = self._world.construction
            if not construction:
                return
            mousePoint = fife.ScreenPoint(evt.getX(), evt.getY())
            location = self._world.getLocationAt(mousePoint)
            if not construction.agent:
                ## Initialize instance
                construction.createInstance(location)

            if construction.teleport(location):
                self._world.cursorHandler.setCursor(_CUR_DEFAULT)
            else:
                self._world.cursorHandler.setCursor(_CUR_CANNOT)


_CUR_DEFAULT, _CUR_ATTACK, _CUR_CANNOT = xrange(3)


class StrategicWorld(World):
    """
    The world!

    This class handles:
      setup of map view (cameras ...)
      loading the map

    That's obviously too much, and should get factored out.
    """
    def __init__(self, engine, settings):
        super(StrategicWorld, self).__init__(engine, settings)

        self.listener = StrategicListener(self)
        self.listener.attach()

        self.scene = StrategicScene(self, self.engine)

        self.HUD = StrategicHUD(self)
        self.HUD.show()

        self.construction = None


    def handleCursor(self):
        '''
        Changes the cursor according to the mode.
        :return:
        '''
        pass
        '''
        if self.mode == _MODE_BUILD:
            if not self.construction:
                return

            mousepoint = fife.ScreenPoint(self.mousePos[0], self.mousePos[1])
            mouseLocation = self.getLocationAt(mousepoint)
            trajectory = Trajectory(self.scene.instance_to_agent[self.activeUnit], self.cameras['main'], self,0)
            # print "Is is reachable?"
            self.cursorHandler.setCursor(_CUR_CANNOT)
            if trajectory.isInRange(mouseLocation):
                if trajectory.hasClearPath(mouseLocation):
                    # print "Changing cursor"
                    self.cursorHandler.setCursor(_CUR_ATTACK)

        else:
            self.cursorHandler.setCursor(_CUR_DEFAULT)
        '''

    def setMode(self, mode):
        '''
        Sets the current runtime tactical mode.
        :param mode: _MODE_DEFAULT, _MODE_ATTACK, _MODE_DROPSHIP
        :return:
        '''

        self.mode = mode
        if mode == _MODE_BUILD:
            self.listener._cellSelectionRenderer.setEnabled(False)
        # Change cursor type
        # dictionary containing {mode:cursor}
        # cursor = self.engine.getCursor()
        # cursorfile = self.settings.get("rio", "CursorAttack")
        # cursorImage = cursor.getImage()


    def startBuilding(self, buildingName):
        '''
        Starts the building mode.
        :return:
        '''

        if self.construction:
            # get rid of the already loaded instance:
            self.stopBuilding()

        self.construction = self.scene.unitLoader.createBuilding(buildingName)
        self.setMode(_MODE_BUILD)
        # self.scene.build()

    def stopBuilding(self):
        '''
        Handles the transition from contructing to default.
        :return:
        '''

        if self.construction:
            # Destroy the construction first!
            # self._world.construction.remove()
            if self.construction.agent:
                self.scene.agentLayer.deleteInstance(self.construction.agent)
                self.construction.__del__()
            self.construction = None
            self.selectUnit(None)

        self.setMode(_MODE_DEFAULT)
        self.cursorHandler.setCursor(_CUR_DEFAULT)