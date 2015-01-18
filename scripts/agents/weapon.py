__author__ = 'cos'


# _LIGHT_WEAPON, _HEAVY_WEAPON = (0,1)
_LWEAPON, _HWEAPON = xrange(2)

import unit
from fife.extensions.fife_settings import Setting

TDS = Setting(app_name="rio_de_hola")


class Weapon(object):
    """
	Weapon

	This class is a super class and is meant to be inherited and
	not used directly.  You should implement fire() in the sub-
	class.
	        """

    def __init__(self, world):
        self._world = world
        # self._layer = self._world.objectlayer()
        self._firerate = None  # Number of AP to fire
        self._type = None  # Type of weapon (Heavy or Light)
        self._damageContact = 0  # Damage produced by this weapon.
        self._damageClose = 0
        self._damageFar = 0
        self._soundclip = None
        self._accuracy = 90  # % Accuracy
        # self._dmgType = None
        self._trajectory = None  # Normal/Balistic
        self._name = None
        self._display = None  # Animation
        self._range = None


    def fire(self, location):
        """
        Fires the weapon in the specified direction.
        To be rewritten
        """
        # self._world.applyDamage(location, self._damageContact)

        ##Test: Spawn a unit.

        hsquad = unit.HumanSquad(TDS, self._world.model, "Jon", self._world.agentlayer, uniqInMap=False)


class LightWeapon(Weapon):
    def __init__(self, world):
        super(LightWeapon, self).__init__(world)
        self._type = _LWEAPON


class HeavyWeapon(Weapon):
    def __init__(self, world):
        super(HeavyWeapon, self).__init__(world)
        self._type = _HWEAPON


class Gun(LightWeapon):
    def __init__(self, world, fireRate, range, damageContact, damageClose=0, damageFar=0):
        super(Gun, self).__init__(world)
        self._range = range
        self._damageContact = damageContact  # Damage produced by this weapon.
        self._damageClose = damageClose
        self._damageFar = damageFar
        self._firerate = fireRate