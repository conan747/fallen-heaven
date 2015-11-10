# ###################################################
# Copyright (C) 2008-2014 The Unknown Horizons Team
# team@unknown-horizons.org
# This file is part of Unknown Horizons.
#
# Unknown Horizons is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the
# Free Software Foundation, Inc.,
# 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
# ###################################################

import math
import time
from fife import fife



class View(object):
    """Class that takes care of all the camera and rendering stuff."""

    def __init__(self, world, engine):
        #super(View, self).__init__()
        self.world = world
        self.engine = engine
        self.model = self.engine.getModel()
        self.cameras = {}
        self.layers = {}



    def load(self, map):
        # NOTE: this is no class function, since view is initiated before loading
        self.map = map
        #Set background color
        self.engine.getRenderBackend().setBackgroundColor(0,0,0)

        #self.layers = map.getLayers()
        self.map.initializeCellCaches()
        self.map.finalizeCellCaches()
        self.agentLayer = self.map.getLayer('TechdemoMapGroundObjectLayer')
        rect = self.agentLayer.getCellCache().getSize()

        # Make sure layer can't change size on layer.createInstance
        # # This is necessary because otherwise unit movement on the map edges would
        # keep changing the units' layer size.
        for layer in self.map.getLayers():
            self.layers[layer.getId()] = layer
            cellCache = layer.getCellCache()
            if cellCache:
                cellCache.setSize(rect)
                cellCache.setStaticSize(True)


        # camera_prefix = self.filename.rpartition('.')[0] # Remove file extension TODO: Is this really necessary?
        # camera_prefix = camera_prefix.rpartition('/')[2] # Remove path
        # camera_prefix += '_'

        for cam in map.getCameras():
            camera_id = cam.getId()
            print "Camera ID: ", camera_id
            self.cameras[camera_id] = cam
            cam.resetRenderers()

        self.cam = self.cameras["main"]

        self.cam.resetRenderers()
        self.renderer = {}
        for r in ('InstanceRenderer', 'GridRenderer',
                  'CellSelectionRenderer', 'BlockingInfoRenderer', 'FloatingTextRenderer',
                  'QuadTreeRenderer', 'CoordinateRenderer', 'GenericRenderer', "CellRenderer"):
            self.renderer[r] = getattr(fife, r).getInstance(self.cam) if hasattr(fife, r) else self.cam.getRenderer(r)
            self.renderer[r].clearActiveLayers()
            self.renderer[r].setEnabled(r in ('InstanceRenderer', 'GenericRenderer'))
        self.renderer['InstanceRenderer'].activateAllLayers(self.map)
        self.renderer['GenericRenderer'].addActiveLayer(self.agentLayer)
        self.renderer['GridRenderer'].addActiveLayer(self.layers["Ground"])

        #Added by cos
        rend = self.renderer["CellSelectionRenderer"]
        rend.setColor(0,0,0)
        rend.addActiveLayer(self.layers["Ground"])

        ## Start cellRenderer to show instance paths:
        # self.cellRenderer.addActiveLayer(self.scene.agentLayer)
        self.renderer['CellRenderer'].activateAllLayers(self.map)
        self.renderer['CellRenderer'].setEnabledBlocking(True)
        self.renderer['CellRenderer'].setPathColor(0,0,255)
        self.renderer['CellRenderer'].setEnabled(True)

        # Fog of War stuff
        # renderer = fife.CellRenderer.getInstance(self.cameras['main'])
        # renderer.setEnabled(True)
        # renderer.clearActiveLayers()
        # renderer.addActiveLayer(self.scene.map.getLayer('TechdemoMapGroundObjectLayer'))
        # concimg = self.engine.getImageManager().load("misc/black_cell.png")
        # maskimg = self.engine.getImageManager().load("misc/mask_cell.png")
        # renderer.setConcealImage(concimg)
        # renderer.setMaskImage(maskimg)
        # renderer.setFogOfWarLayer(self.scene.map.getLayer('TechdemoMapGroundObjectLayer'))

        #disable FoW by default.  Users can turn it on with the 'f' key.
        # renderer.setEnabledFogOfWar(False)


        # #Setup autoscroll
        # horizons.globals.fife.pump.append(self.do_autoscroll)
        # self.time_last_autoscroll = time.time()
        # self._autoscroll = [0, 0]
        # self._autoscroll_keys = [0, 0]

        # res = db("SELECT zoom, rotation, location_x, location_y FROM view")
        # if not res:
        # 	# no view info
        # 	return
        # zoom, rotation, loc_x, loc_y = res[0]
        # self.zoom = zoom
        # self.set_rotation(rotation)
        # self.center(loc_x, loc_y)


    def setVisual(self, agents):
        '''
        Start cellRenderer to show instance paths
        :return:
        '''
        renderer = self.renderer['CellRenderer']
        [renderer.addPathVisual(unit.instance) for unit in agents]
        renderer.setEnabledPathVisual(True)
        renderer.setEnabled(True)



    def moveCamera(self, speedVector):
        ''' Checks if the mouse is on the edge of the screen and moves the camera accordingly'''

        mainCamera = self.cam
        #speedVector = (-0.5,0)
        angle = mainCamera.getRotation()
        currentLocation = mainCamera.getLocation()
        # print "Close to the edge!"
        vector = fife.DoublePoint3D(speedVector[0] * math.cos(angle) - speedVector[1] * math.sin(angle),
                                    speedVector[0] * math.sin(angle) + speedVector[1] * math.cos(angle),0)
        currentPoint = currentLocation.getMapCoordinates()
        newPoint = currentPoint + vector
        currentLocation.setMapCoordinates(newPoint)

        if mainCamera.getMatchingInstances(currentLocation):
            mainCamera.setLocation(currentLocation)


    def end(self):
        # horizons.globals.fife.pump.remove(self.do_autoscroll)
        self.model.deleteMaps()
        #super(View, self).end()

    def addPathVisual(self, instance):
        self.renderer["CellRenderer"].addPathVisual(instance)

    def removePathVisual(self, instance):
        self.renderer["CellRenderer"].removePathVisual(instance)


    def center(self, x, y):
        """Sets the camera position
        @param center: tuple with x and y coordinate (float or int) of tile to center
        """
        loc = self.cam.getLocationRef()
        pos = loc.getExactLayerCoordinatesRef()
        pos.x = x
        pos.y = y
        self.cam.refresh()
        #self._changed()

    def scroll(self, x, y):
        """Moves the camera across the screen
        @param x: int representing the amount of pixels to scroll in x direction
        @param y: int representing the amount of pixels to scroll in y direction
        """
        loc = self.cam.getLocation()
        pos = loc.getExactLayerCoordinatesRef()
        cell_dim = self.cam.getCellImageDimensions()

        if x != 0:
            new_angle = math.pi * self.cam.getRotation() / 180.0
            zoom_factor = self.cam.getZoom() * cell_dim.x * horizons.globals.fife.get_uh_setting('ScrollSpeed')
            pos.x += x * math.cos(new_angle) / zoom_factor
            pos.y += x * math.sin(new_angle) / zoom_factor
        if y != 0:
            new_angle = math.pi * self.cam.getRotation() / -180.0
            zoom_factor = self.cam.getZoom() * cell_dim.y * horizons.globals.fife.get_uh_setting('ScrollSpeed')
            pos.x += y * math.sin(new_angle) / zoom_factor
            pos.y += y * math.cos(new_angle) / zoom_factor

        if pos.x > self.world.max_x:
            pos.x = self.world.max_x
        elif pos.x < self.world.min_x:
            pos.x = self.world.min_x

        if pos.y > self.world.max_y:
            pos.y = self.world.max_y
        elif pos.y < self.world.min_y:
            pos.y = self.world.min_y

        self.cam.setLocation(loc)
        for i in ['speech', 'effects']:
            emitter = horizons.globals.fife.sound.emitter[i]
            if emitter is not None:
                emitter.setPosition(pos.x, pos.y, 1)
        if horizons.globals.fife.get_fife_setting("PlaySounds"):
            horizons.globals.fife.sound.soundmanager.setListenerPosition(pos.x, pos.y, 1)
        self._changed()

    def _prepare_zoom_to_cursor(self, zoom):
        """Change the camera's position to accommodation zooming to the specified setting."""
        def middle(click_coord, scale, length):
            mid = length / 2.0
            return int(round(mid - (click_coord - mid) * (scale - 1)))

        scale = self.cam.getZoom() / zoom
        x, y = horizons.globals.fife.cursor.getPosition()
        new_x = middle(x, scale, horizons.globals.fife.engine_settings.getScreenWidth())
        new_y = middle(y, scale, horizons.globals.fife.engine_settings.getScreenHeight())
        screen_point = fife.ScreenPoint(new_x, new_y)
        map_point = self.cam.toMapCoordinates(screen_point, False)
        self.center(map_point.x, map_point.y)

    def zoom_out(self, track_cursor=False):
        zoom = self.cam.getZoom() * VIEW.ZOOM_LEVELS_FACTOR
        if zoom < VIEW.ZOOM_MIN:
            zoom = VIEW.ZOOM_MIN
        if track_cursor:
            self._prepare_zoom_to_cursor(zoom)
        self.zoom = zoom

    def zoom_in(self, track_cursor=False):
        zoom = self.cam.getZoom() / VIEW.ZOOM_LEVELS_FACTOR
        if zoom > VIEW.ZOOM_MAX:
            zoom = VIEW.ZOOM_MAX
        if track_cursor:
            self._prepare_zoom_to_cursor(zoom)
        self.zoom = zoom

    @property
    def zoom(self):
        return self.cam.getZoom()

    @zoom.setter
    def zoom(self, value):
        self.cam.setZoom(value)

    def rotate_right(self):
        self.cam.setRotation((self.cam.getRotation() - 90) % 360)

    def rotate_left(self):
        self.cam.setRotation((self.cam.getRotation() + 90) % 360)

    def set_rotation(self, rotation):
        self.cam.setRotation(rotation)
        self._changed()

    def get_displayed_area(self):
        """Returns the coords of what is displayed on the screen as Rect"""
        coords = self.cam.getLocationRef().getLayerCoordinates()
        cell_dim = self.cam.getCellImageDimensions()
        engineSettings = self.engine.getSettings()
        screenSize = (engineSettings.getScreenWidth(), engineSettings.getScreenHeight())

        width_x = screenSize[0] // cell_dim.x + 1
        width_y = screenSize[1] // cell_dim.y + 1
        screen_width_as_coords = (width_x // self.zoom, width_y // self.zoom)
        return Rect.init_from_topleft_and_size(coords.x - (screen_width_as_coords[0] // 2),
                                               coords.y - (screen_width_as_coords[1] // 2),
                                               *screen_width_as_coords)
