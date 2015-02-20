"""Level editor module."""
import sdl2
import numpy
from enum import Enum, unique
from .enemy import Wave
from .vector import Vector
from .level import Tile


class Editor(object):
    @unique
    class State(Enum):
        """Enumeration of different editor modes."""
        tile = 1
        wave = 2

    def __init__(self, app, level):
        self._state = Editor.State.tile
        self._app = app
        self._level = level

    def draw(self):
        self._level.picking_draw()

        for _, tile in numpy.ndenumerate(self._level.tiles):
            if tile:
                # TODO: Hardcoded phase here
                draw_faces = (0 in tile.waves or self._state != Editor.State.wave)
                tile.draw(faces=draw_faces)

        self._level.base.draw()

    def update(self):
        pass

    def on_keydown(self, key):
        """Handle keydown events."""
        if key == sdl2.SDLK_s:
            self._level.save()
        elif key == sdl2.SDLK_t:
            self._state = Editor.State.tile
        elif key == sdl2.SDLK_w:
            self._state = Editor.State.wave

    def on_text(self, c):
        """Handle text input."""
        pass

    def on_click(self, x, y):
        """Handle a mouse click."""
        tile = self._level.screen_coords_to_tile(Vector(x, y))

        if self._state == Editor.State.tile:
            if tile:
                pass
            else:
                tile_coords = self._level.screen_coords_to_tile_coords(
                    Vector(x, y))
                if self._level.tile_coords_valid(tile_coords):
                    index = self._level.tile_coords_to_array_index(tile_coords)
                    self._level.tiles[index.y, index.x] = Tile(self._app,
                                                               self._level.cam,
                                                               tile_coords, 0)
        elif self._state == Editor.State.wave:
            # TODO: Hardcoded phase
            if tile and 0 not in tile.waves:
                # Extend the wave list if it is not long enough.
                wave = Wave(self._app, self._level, tile)
                # TODO: Hardcoded phase
                self._level.waves += [[]] * (len(self._level.waves) - (0 + 1))
                self._level.waves[0].append(wave)
                tile.waves[0] = wave