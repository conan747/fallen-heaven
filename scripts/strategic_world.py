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
from world import *

from gui.huds import StrategicHUD
from combat import Trajectory
from scripts.strategic_scene import StrategicScene



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


    def clickRecycle(self, clickpoint):
        # self.hide_instancemenu()

        instances = self._world.getInstancesAt(clickpoint)
        print "selected instances on agent layer: ", [i.getObject().getId() for i in instances]
        print "Found " , instances.__len__(), "instances"

        if instances:
            for instance in instances:
                id = instance.getFifeId()
                print "Instance: ", id
                if id in self._world.scene.instance_to_agent.keys():
                    agent = self._world.scene.instance_to_agent[id]
                    print "Recycling: ", agent.agentName
                    agent.die()
                    # refund the cost
                    cost = int(agent.properties["Cost"])
                    self._world.deductCredits(-cost)
                    self._world.HUD.updateUI()
            ## TODO: Handle situation when recycling a building containing storage.
            ## TODO: Reduce refund when building is built.


    def clickDefault(self, clickpoint):

        super(StrategicListener, self).clickDefault(clickpoint)
        self._world.HUD.updateUI()


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

        elif self._world.mode == self._world.MODE_BUILD:
            construction = self._world.construction
            if not construction:
                return
            mousePoint = fife.ScreenPoint(evt.getX(), evt.getY())
            location = self._world.getLocationAt(mousePoint)
            if not construction.agent:
                ## Initialize instance
                construction.createInstance(location)

            if construction.teleport(location):
                self._world.cursorHandler.setCursor(self._world.cursorHandler.CUR_DEFAULT)
            else:
                self._world.cursorHandler.setCursor(self._world.cursorHandler.CUR_CANNOT)




class StrategicWorld(World):
    """
    The world!

    This class handles:
      setup of map view (cameras ...)
      loading the map

    That's obviously too much, and should get factored out.
    """
    def __init__(self, universe, planet):
        super(StrategicWorld, self).__init__(universe, planet)

        self.listener = StrategicListener(self)
        self.listener.attach()

        self.scene = StrategicScene(self, self.engine)

        self.HUD = StrategicHUD(self)
        self.HUD.show()

        self.construction = None


    def startRecycling(self):
        '''
        Starts the recycling mode.
        :return:
        '''
        self.setMode(self.MODE_RECYCLE)

    def startBuilding(self, buildingName):
        '''
        Starts the building mode.
        :return:
        '''

        if self.construction:
            # get rid of the already loaded instance:
            self.stopBuilding()

        self.construction = self.scene.unitLoader.createBuilding(buildingName)
        self.setMode(self.MODE_BUILD)
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

        self.setMode(self.MODE_DEFAULT)