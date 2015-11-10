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
from scripts.common.common import ProgrammingError

class Agent(fife.InstanceActionListener):
    def __init__(self, unitName, agentType, world):
        fife.InstanceActionListener.__init__(self)
        # self.settings = settings
        # self.model = model
        self.agentName = None
        self.unitName = unitName
        self.agentType = agentType
        # self.layer = layer
        self.world = world
        self.instance = None

        self.properties = {}
        self.movement = None
        self.lightWeapon = None
        self.heavyWeapon = None

        self.projectile = None


        self.health = 0

    def getFifeId(self):
        if self.instance:
            return self.instance.getFifeId()


    def createInstance(self, location):
        '''
        Creates the instance of the object on the map.
        :param location: Location where the instance will be.
        :return:
        '''

        if type(location) is fife.Location:
            point = location.getLayerCoordinates()
        else:
            point = fife.Point3D(location[0], location[1], location[2])

        self.nameSpace = "fallen"
        object = self.world.model.getObject(self.unitName, self.nameSpace)
        if not object:
            print "Error! No ", self.unitName ,"found in the object library"

        object = self.setWalkableAreas(object)
        object.setBlocking(True)

        self.instance = self.world.scene.agentLayer.createInstance(object, point)
        self.instance.setCellStackPosition(0)

        if self.unitName:
            fifeID = self.instance.getFifeId()
            self.agentName = self.unitName + ":" + str(fifeID)

            self.instance.setId(self.agentName)
            print "Created ", self.instance.getId()

        self.instance.addActionListener(self)


    def setWalkableAreas(self, object):

        # Set walkable area:
        object.addWalkableArea("land")

        if self.properties.has_key("Movement"):
            movementType = self.properties["Movement"]
            if movementType == "HOVER":
                object.addWalkableArea("water")

        return object



    def selectInstance(self, instanceName):
        '''
        Looks for an instance with the same name in the map and associates it with this agent.
        :param instanceName: Name of the instance in the loaded map on the "activeLayer"
        :return: bool, true if it could be loaded.
        '''
        layer = self.world.scene.agentLayer
        self.instance = layer.getInstance(instanceName)
        #object = self.instance.getObject()

        if self.instance:
            self.agentName = instanceName
            self.instance.addActionListener(self)
            return True
        else:
            return False


    def onInstanceActionFinished(self, instance, action):
        print "Action Finished!"
        self.world.HUD.updateUI()
        self.world.busy = False
        #TODO: Add here the trajectory erasing instead after run?

    def onInstanceActionFrame(self, instance, action, frame):
        print "Action frame" , frame

    def start(self):
        pass


    def onInstanceActionCancelled(self, instance, action):
        print "Action cancelled!"


    def idle(self):
        pass
        # self.instance.actOnce('stand')

    def die(self):
        pass

    def printProperties(self):
        print self.properties

    def getDamage(self, dmg):
        print "Previous health: " , self.health
        print "Dealing ", dmg, " damage!"
        self.health -= dmg
        if self.health <= 0:
            self.die()


    def resetAP(self):
        pass