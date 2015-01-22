__author__ = 'cos'


import os

from fife import fife
from fife.extensions import pychan
from fife.extensions.pychan import widgets
from fife.extensions.pychan.fife_pychansettings import FifePychanSettings

from xml.sax.saxutils import XMLGenerator
from xml.sax.xmlreader import AttributesNSImpl
# from fife.extensions.pychan.internal import get_manager


class TacticalHUD(object):
    def __init__(self, world):
        self._world = world
        self._widget = pychan.loadXML('gui/tactical_hud.xml')

        # self._image = world.engine.getImageManager().load("./gui/HUDs/combat_botton.png")
        # self._guiImage = fife.GuiImage(self._image)
        # wid = self._widget.findChild(name="high_score")
        # print wid._getName()
        # wid.setBackgroundImage(self._guiImage)
        # print "Image size:" , self._image.getWidth()
        #
        #
        #
        # print "Image size" , self._guiImage.getWidth(), self._guiImage.getHeight()

        # self._widget.position = (0, 0)
        self._widget.mapEvents({
                'nextTurnButton' : self._world.onSkipTurnPress,
                'attackLightButton' : self._world.onAttackButtonPressed
        })


    def show(self):
        self._widget.show()

    def hide(self):
        self._widget.hide()

    # def setFPSText(self, text):
    #     self._fpstext.text = text



class StrategicHUD(object):
    def __init__(self, world):
        self._world = world
        self._widget = pychan.loadXML('gui/strategic_hud.xml')

        # self._image = world.engine.getImageManager().load("./gui/HUDs/combat_botton.png")
        # self._guiImage = fife.GuiImage(self._image)
        # wid = self._widget.findChild(name="high_score")
        # print wid._getName()
        # wid.setBackgroundImage(self._guiImage)
        # print "Image size:" , self._image.getWidth()
        #
        #
        #
        # print "Image size" , self._guiImage.getWidth(), self._guiImage.getHeight()

        # self._widget.position = (0, 0)
        self._widget.mapEvents({
                'toUniverseButton' : self._world.testBuilding,
                # 'attackLightButton' : self._world.onAttackButtonPressed
        })


    def show(self):
        self._widget.show()

    def hide(self):
        self._widget.hide()

    # def setFPSText(self, text):
    #     self._fpstext.text = text


