#!/usr/bin/env python

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
# This is the rio de hola client for FIFE.

import sys, os, re, math, random, shutil

fife_path = os.path.join('..','..','engine','python')
if os.path.isdir(fife_path) and fife_path not in sys.path:
    sys.path.insert(0,fife_path)

from fife import fife
print "Using the FIFE python module found here: ", os.path.dirname(fife.__file__)

from fife.extensions import *
from scripts.universe import *
from scripts.common import eventlistenerbase
from fife.extensions import pychan
from fife.extensions.pychan.pychanbasicapplication import PychanApplicationBase
from fife.extensions.pychan.fife_pychansettings import FifePychanSettings
from fife.extensions.pychan import widgets
from fife.extensions.pychan.internal import get_manager
from fife.extensions.fife_settings import Setting
from fife.extensions.fife_utils import getUserDataDirectory


TDS = FifePychanSettings(app_name="fallen")

class ApplicationListener(eventlistenerbase.EventListenerBase):
    def __init__(self, engine, universe, settings):
        super(ApplicationListener, self).__init__(engine,regKeys=True,regCmd=True, regMouse=False, regConsole=True, regWidget=True)
        self.engine = engine
        self.universe = universe
        self._setting = settings
        self._widget = pychan.loadXML('gui/mainmenu.xml')
        # self.world = world
        engine.getEventManager().setNonConsumableKeys([
                fife.Key.ESCAPE,])

        self.quit = False
        # self.aboutWindow = None

        self._continue = self._widget.findChild(name="continue")
        self._newgame = self._widget.findChild(name="new_game")
        # self._credits = self._widget.findChild(name="credits")
        # self._highscores = self._widget.findChild(name="high_scores")
        self._quit = self._widget.findChild(name="quit")
        self.cont = False

        self._widget.position = (0, 0)

        eventMap = {
            'continue': self.onContinuePressed,
            'new_game': self.onNewGamePressed,
            'settings': self._setting.showSettingsDialog,
            # 'credits': self._world.showCredits,
            # 'high_scores': self._world.showHighScores,
            'quit': self.onQuitButtonPress,
            'load' : self.onLoadPressed
        }

        self._widget.mapEvents(eventMap)
        self._continueMinWidth = self._continue.min_width
        self._continueMinHeight = self._continue.min_height
        self._continueMaxWidth = self._continue.max_width
        self._continueMaxHeight = self._continue.max_height


    def onContinuePressed(self):
        self.hide()
        self.universe.continueGame()

    def onNewGamePressed(self):
        self.hide()
        widget = pychan.VBox()
        buttonCreate = pychan.Button(name="createCampaign", text="Create new campaign", parent=widget)
        buttonJoin = pychan.Button(name="joinCampaign", text="Join a campaign", parent=widget)
        widget.addChildren(buttonCreate, buttonJoin)
        widget.show()
        campaign = Campaign(self.universe)
        def onButtonCreate(wid=widget, campaign=campaign):
            wid.hide(free=True)
            campaign.createCampaign()

        def onButtonJoin(wid=widget, campaign=campaign):
            wid.hide(free=True)
            campaign.joinGame()
            self.cont = True

        widget.mapEvents({"createCampaign" : onButtonCreate,
                          "joinCampaign" : onButtonJoin})


    def onLoadPressed(self):
        self.hide()
        self.universe.load()
        self.cont = True


    def show(self):
        if self.cont:
            self._continue.min_width = self._continueMinWidth
            self._continue.min_height = self._continueMinHeight
            self._continue.max_width = self._continueMaxWidth
            self._continue.max_height = self._continueMaxHeight

        else:
            self._continue.min_width = 0
            self._continue.min_height = 0
            self._continue.max_width = 0
            self._continue.max_height = 0

        self._continue.adaptLayout()
        self._widget.show()


    def hide(self):
        self._widget.hide()

    def isVisible(self):
        return self._widget.isVisible()

    def keyPressed(self, evt):
        print evt
        keyval = evt.getKey().getValue()
        #keystr = evt.getKey().getAsString().lower()
        #consumed = False
        if keyval == fife.Key.ESCAPE:
            self.universe.pauseGame()
            self.show()
            # self.quit = True
            evt.consume()
        elif keyval == fife.Key.F10:
            get_manager().getConsole().toggleShowHide()
            evt.consume()
        # elif keystr == 'p':
        #     self.engine.getRenderBackend().captureScreen('screenshot.png')
        #     evt.consume()
    #
    # def onCommand(self, command):
    #     if command.getCommandType() == fife.CMD_QUIT_GAME:
    #         self.quit = True
    #         command.consume()
    #
    # def onConsoleCommand(self, command):
    #     result = ''
    #     if command.lower() in ('quit', 'exit'):
    #         self.quit = True
    #         result = 'quitting'
    #     elif command.lower() in ( 'help', 'help()' ):
    #         get_manager().getConsole().println( open( 'misc/infotext.txt', 'r' ).read() )
    #         result = "-- End of help --"
    #     else:
    #         result = self.world.onConsoleCommand(command)
    #     if not result:
    #         try:
    #             result = str(eval(command))
    #         except:
    #             pass
    #     if not result:
    #         result = 'no result'
    #     return result

    def onQuitButtonPress(self):
        self.quit = True
        cmd = fife.Command()
        cmd.setSource(None)
        cmd.setCommandType(fife.CMD_QUIT_GAME)
        self.engine.getEventManager().dispatchCommand(cmd)

    # def onAboutButtonPress(self):
    #     if not self.aboutWindow:
    #         self.aboutWindow = pychan.loadXML('gui/help.xml')
    #         self.aboutWindow.mapEvents({ 'closeButton' : self.aboutWindow.hide })
    #         self.aboutWindow.distributeData({ 'helpText' : open("misc/infotext.txt").read() })
    #     self.aboutWindow.show()



class FallenHeaven(PychanApplicationBase):
    '''
    Start here! This class basically creates the universe. It passes the pump call to it too.
    It also creates the Main Menu which is saved in self.listener.
    '''
    def __init__(self):
        super(FallenHeaven, self).__init__(TDS)
        self.universe = Universe(self.engine, TDS)
        self.listener = ApplicationListener(self.engine, self.universe, TDS)
        self.listener.show()

    def createListener(self):
        pass # already created in constructor

    def _pump(self):
        if self.listener.quit:
            if self.universe:
                self.universe.save()
            self.breakRequested = True
        else:
            self.universe.pump()

def main():
    app = FallenHeaven()
    app.run()


if __name__ == '__main__':

    if FifePychanSettings(app_name="fallen").get("FIFE", "UsePsyco"):
            # Import Psyco if available
            try:
                import psyco
                psyco.full()
                print "Psyco acceleration in use"
            except ImportError:
                print "Psyco acceleration not used"
    else:
            print "Psyco acceleration not used"
    main()
