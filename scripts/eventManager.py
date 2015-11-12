__author__ = 'jon'



class Graveyard(fife.InstanceActionListener):
    '''
    Pure virtual class. Handles proper destruction of instances.
    '''
    def __init__(self, layer):
        super(Graveyard, self).__init__(self)

        self.layer = layer
        self.instances = []
        self.layer = None
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
            instance.removeActionListener(self)
            self.layer.deleteInstance(instance)


class ProjectileGraveyard(Graveyard):
    '''
    Handles the destruction of projectiles.
    '''
    def __init__(self, layer):
        super(ProjectileGraveyard, self).__init__(layer)


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



class EventManager(object):
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

    def nex(self):
        '''
        Handles the next thing to do.
        :return:
        '''

        self.update()

        if not self.projectileGraveyard.isEmpty():
            self.projectileGraveyard.next()
            return

        if not self.unitGraveyard.isEmpty():
            self.unitGraveyard.next()
            return

        ## Handle retaliation.
        if self.retaliation:
            if not self.retaliation.blocked:
                self.retaliation.next()
