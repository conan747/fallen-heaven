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

from gui.huds import TacticalHUD
from combat import Trajectory
from scripts.tactic_scene import TacticScene




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
        trajectory = Trajectory(self._world.scene.instance_to_agent[self._world.activeUnit], self._world,0)
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

        elif self._world.activeUnit:
            # there was a unit selected and an empty cell has been clicked
            agent = self._world.scene.instance_to_agent[self._world.activeUnit]
            if agent.agentType == "Unit":
                # move the unit if possible
                self._world.scene.instance_to_agent[self._world.activeUnit].run(self._world.getLocationAt(clickpoint))
            else:
                # we assume it's a building -> deselect it.
                self._world.selectUnit(None)



class TacticWorld(World):
    """
    The world!

    This class handles:
      setup of map view (cameras ...)
      loading the map

    That's obviously too much, and should get factored out.
    """
    def __init__(self, universe, planet):
        super(TacticWorld, self).__init__(universe, planet)

        self._nextTurnWindow = None


        self.listener = TacticListener(self)
        self.listener.attach()

        self.faction = self.universe.faction

        self.scene = TacticScene(self, self.engine)

        self.HUD = TacticalHUD(self)
        self.HUD.show()


    def onAttackButtonPressed(self):
        if self.activeUnit:
            self.setMode(self.MODE_ATTACK)
