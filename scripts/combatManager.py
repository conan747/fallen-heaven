__author__ = 'jon'

from fife import fife

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
        instance.addActionListener(self)

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
    def __init__(self, layer):
        super(ProjectileGraveyard, self).__init__(layer)

    def onInstanceActionFinished(self, instance, action):
        if action.getId() == "move":
            self.instances.append(instance)
            self.busy = False
            self.projectile = None

    def add(self, instance):
        instance.addActionListener(self)
        self.busy = True

    def addProjectile(self, projectile):
        '''
        Adds the projectile and waits till it moves.
        '''
        self.projectile = projectile
        self.add(projectile.getInstance())


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




class Projectile(fife.InstanceActionListener):

    def __init__(self, parent, world, origin, destination, callback=None):

        super(Projectile, self).__init__()

        self.callback = callback
        self.world = world
        self.layer = world.map.getLayer("TrajectoryLayer")

        object = world.model.getObject("SBT", "fallen")
        print "Attacking from: " , origin.getLayerCoordinates()
        originCoords = origin.getExactLayerCoordinates()
        self.instance = self.layer.createInstance(object, originCoords)
        self.instance.thisown = 0
        self.instance.addActionListener(self)
        self.destination = fife.Location(self.layer)
        self.destination.setLayerCoordinates(destination.getLayerCoordinates())
        print "To: ", self.destination.getLayerCoordinates()
        print "\n\nbullet created!"

        self.move()

    def getInstance(self):
        return self.instance

    def move(self):
        if self.destination.isValid():
            self.instance.move("move", self.destination, 5)

    def onInstanceActionFinished(self, instance, action):
        print action.getId()
        if action.getId() == "move": # and self.start:
            print "\n\nDestroying bullet"
            self.instance.removeActionListener(self)
            print "Cleaning up."
            #self.world.projectileGraveyard.add(self.instance)
            self.instance = None
            if self.callback:
                self.callback()
            self.__del__() # Is this necessary?


    def onInstanceActionCancelled(self, instance, action):
        print "Action cancelled!"

    def onInstanceActionFrame(self, instance, action, frame):
        print "Action frame" , frame



class CombatManager(object):
    '''
    Keeps track of the events in world. Blocks world execution until all the events have been taken care of.
    '''

    def __init__(self, world):
        self.world = world


    def update(self):
        '''
        Updates the information from the world.
        :return:
        '''
        self.unitGraveyard = self.world.unitGraveyard
        self.projectileGraveyard = self.world.projectileGraveyard
        self.retaliation = self.world.retaliation

        self.paused = False

    def next(self):
        '''
        Handles the next thing to do.
        :return:
        '''

        self.update()

        if self.paused:
            return

        if self.projectileGraveyard and not self.projectileGraveyard.isEmpty():
            self.projectileGraveyard.next()
            return

        if self.unitGraveyard and not self.unitGraveyard.isEmpty():
            self.unitGraveyard.next()
            return

        ## Handle retaliation.
        if self.retaliation:
            if not self.retaliation.blocked:
                self.retaliation.next()

    def combatStarted(self):
        self.paused = True

    def resume(self):
        self.paused = False

    def addProjectile(self, unit, origin, destination, callback=None):
        '''
        Adds a projectile to the scene and takes care of its construction and destruction.
        :param unit: Unit that is firing.
        :param origin: Location where the projectile will start from
        :param destination: Location where the projectile will travel
        :param callback: What will be run right after it ends.
        :return:
        '''
        projectile = Projectile(unit, self.world ,origin, destination, callback)
        self.projectileGraveyard.addProjectile(projectile)