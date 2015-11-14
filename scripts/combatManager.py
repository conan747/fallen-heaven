__author__ = 'jon'

from fife import fife
from combat import *

class Graveyard(fife.InstanceActionListener):
    '''
    Pure virtual class. Handles proper destruction of instances.
    '''
    def __init__(self, layer):
        super(Graveyard, self).__init__()

        self.layer = layer
        self.instances = []
        self.busy = False

    def add(self, instance):
        self.instances.append(instance)
        # instance.addActionListener(self)

    def next(self):
        if not self.busy:
            self.removeDead()

    def onInstanceActionFinished(self, instance, action):
        pass

    def onInstanceActionFrame(self, instance, action, frame):
        pass

    def onInstanceActionCancelled(self, instance, action):
        pass

    def isEmpty(self):
        return ( len(self.instances) == 0 )

    def removeDead(self, instances=None):
        if not instances:
            instances = self.instances

        while instances:
            instance = instances.pop()
            if not self.isInLayer(instance):
                continue
            instance.removeActionListener(self)
            self.layer.deleteInstance(instance)

    def isInLayer(self, instance):
        '''
        Checks if an instance is in the layer.
        '''
        instances = self.layer.getInstances()
        id = instance.getFifeId()
        for inst in instances:
            if inst.getFifeId() == id:
                return True

        return False


class ProjectileGraveyard(Graveyard):
    '''
    Handles the destruction of projectiles.
    '''
    def __init__(self, layer, combatManager):
        super(ProjectileGraveyard, self).__init__(layer)
        # self.combatManager = combatManager
        # self.projectile = None

    # def onInstanceActionFinished(self, instance, action):
    #     if action.getId() == "move":
    #         print "ProjectileGraveyard: projectile moved."
    #         self.instances.append(instance)
    #         self.busy = False
    #         self.projectile = None
    #         self.combatManager.resume()

    # def add(self, instance):
    #     instance.addActionListener(self)
    #     self.busy = True

    # def addProjectile(self, projectile):
    #     '''
    #     Adds the projectile and waits till it moves.
    #     '''
    #     self.projectile = projectile
    #     self.add(projectile.getInstance())


class UnitGraveyard(Graveyard):
    '''
    Handles destruction of units (including explosions).
    '''

    def __init__(self, unitLayer):
        super(UnitGraveyard, self).__init__(unitLayer)
        self.toExplode = []
        self.toDelete = []

    def isEmpty(self):
        return not (self.toExplode or self.toDelete)

    def next(self):
        if self.busy:
            return

        self.removeDead(self.toDelete)

        if self.toExplode:
            self.explodeUnit(self.toExplode.pop())


    def add(self, instance, explode=False):
        if explode:
            self.toExplode.append(instance)
        else:
            self.toDelete.append(instance)


    def explodeUnit(self, instance):
        '''
        Shows the explosion animation
        '''
        instance.addActionListener(self)
        instance.actOnce("explode")
        self.busy = True

    def onInstanceActionFinished(self, instance, action):
        if action.getId() == "explode":
            instance.removeActionListener(self)
            self.toDelete.append(instance)
            self.busy = False


class CombatManager(object):
    '''
    Keeps track of the events in world. Blocks world execution until all the events have been taken care of.
    '''

    def __init__(self, world):
        self.world = world
        self.retaliation = None
        self.projectile = None
        self.inCombat = False


    def next(self):
        '''
        Handles the next thing to do.
        :return:
        '''

        # if self.paused:
        #     return
        if self.projectile:
            if self.projectile.active:
                self.projectile.pump()
                return
            else:
                self.projectile = None

        if self.world.projectileGraveyard and not self.world.projectileGraveyard.isEmpty():
            self.world.projectileGraveyard.next()
            return

        if self.world.unitGraveyard and not self.world.unitGraveyard.isEmpty():
            self.world.unitGraveyard.next()
            return

        ## Handle retaliation.
        if self.retaliation:
            if self.retaliation.active:
                if not self.retaliation.blocked:
                    self.retaliation.next()
                    return
            else:
                self.retaliation = None

        self.combatFinished()

    def newCombat(self, attackerAgent):
        '''
        Starts a combat round with retaliation.
        :param attackerAgent: Agent that attacks
        :return:
        '''
        if self.inCombat:
            return
        self.inCombat = True
        self.retaliation = Retaliation(self.world, attackerAgent)

    def resume(self):
        self.paused = False

    def combatFinished(self):
        self.inCombat = False
        self.retaliation = None

    def addProjectile(self, origin, destination, weapon=None, callback=None):
        '''
        Adds a projectile to the scene and takes care of its construction and destruction.
        :param unit: Unit that is firing.
        :param origin: Location where the projectile will start from
        :param destination: Location where the projectile will travel
        :param callback: What will be run right after it ends.
        :return:
        '''
        self.projectile = Projectile(self.world, origin, destination, weapon=weapon, callback=callback)
        if self.retaliation:
            self.retaliation.unblock()
        # self.paused = True