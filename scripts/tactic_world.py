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
from world import *

TDS = Setting(app_name="rio_de_hola")


_MODE_DEFAULT, _MODE_ATTACK, _MODE_DROPSHIP = xrange(3)


class TacticListener(WorldListener):
    """
	Main game listener.  Listens for Mouse and Keyboard events.

	This class also has the ability to attach and detach itself from
	the event manager in cases where you do not want input processed (i.e. when
	the main menu is visible).  It is NOT attached by default.
	"""

    def __init__(self, world):
        super(TacticListener, self).__init__(world)


    def clickAttack(self, clickpoint):
        '''
        Handles the click action when attack is selected.
        :return:
        '''

        if not self._world.activeUnit:
            print "No active unit selected!"
            return

        clickLocation = self._world.getLocationAt(clickpoint)
        trajectory = Trajectory(self._world.scene.instance_to_agent[self._world.activeUnit], self._world.cameras['main'], self._world,0)
        # print "Is is reachable?"
        if trajectory.isInRange(clickLocation):

        # print "Calculating Clear path:"
            if trajectory.hasClearPath(clickLocation):
                self._world.scene.instance_to_agent[self._world.activeUnit].attack(clickLocation)


    def clickDefault(self, clickpoint):
        # self.hide_instancemenu()

        instances = self._world.getInstancesAt(clickpoint)
        print "selected instances on agent layer: ", [i.getObject().getId() for i in instances]
        print "Found " , instances.__len__(), "instances"

        if instances:
            # self.activeUnit = None
            print "Current turn:" , self._world.scene.currentTurn
            for instance in instances:
                id = instance.getFifeId()
                print "Instance: ", id
                print "Is it in: ", self._world.scene.factionUnits[self._world.scene.currentTurn]
                if id in self._world.scene.factionUnits[self._world.scene.currentTurn]:
                    print "Instance: " , id, " is owned by this player!"
                    #self.activeUnit = id
                    self._world.selectUnit(id)
        if self._world.activeUnit:
            self._world.scene.instance_to_agent[self._world.activeUnit].run(self._world.getLocationAt(clickpoint))




    def mouseMoved(self, evt):

        self._world.mousePos = (evt.getX(), evt.getY())
        # renderer = fife.InstanceRenderer.getInstance(self.cameras['main'])
        # renderer.removeAllOutlines()

        # pt = fife.ScreenPoint(evt.getX(), evt.getY())
        # instances = self.getInstancesAt(pt);
        # for i in instances:
        #     if i.getObject().getId() in ('girl', 'beekeeper'):
        #         renderer.addOutlined(i, 173, 255, 47, 2)


## TODO: Make a World class to be inherited.

_CUR_DEFAULT, _CUR_ATTACK, _CUR_CANNOT = xrange(3)

class TacticWorld(World):
    """
    The world!

    This class handles:
      setup of map view (cameras ...)
      loading the map

    That's obviously too much, and should get factored out.
    """
    def __init__(self, engine, settings):
        super(TacticWorld, self).__init__(engine, settings)

        self._nextTurnWindow = None


        self.listener = TacticListener(self)
        self.listener.attach()



        self.scene = TacticScene(self, self.engine)

        self.tacticalHUD = TacticalHUD(self)
        self.tacticalHUD.show()


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
            trajectory = Trajectory(self.scene.instance_to_agent[self.activeUnit], self.cameras['main'], self,0)
            # print "Is is reachable?"
            self.cursorHandler.setCursor(_CUR_CANNOT)
            if trajectory.isInRange(mouseLocation):
                if trajectory.hasClearPath(mouseLocation):
                    # print "Changing cursor"
                    self.cursorHandler.setCursor(_CUR_ATTACK)

        else:
            self.cursorHandler.setCursor(_CUR_DEFAULT)

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

    def onAttackButtonPressed(self):
        if self.activeUnit:
            self.setMode(_MODE_ATTACK)

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