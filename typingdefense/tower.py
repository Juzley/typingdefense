"""Module containing the different towers that can be placed by the player."""
import OpenGL.GL as GL
from .glutils import Hex, ShaderInstance
from .vector import Vector
from .util import Colour


class Tower(object):
    def __init__(self, app, level, tile, colour):
        self._shader = ShaderInstance(
            app, 'level.vs', 'level.fs',
            [('transMatrix', GL.GL_FLOAT_MAT4,
              level.cam.trans_matrix_as_array()),
             ('colourIn', GL.GL_FLOAT_VEC4, colour)])
        self._hex = Hex(Vector(tile.x, tile.y, tile.top), 0.5, 2, stacks=4)

    def update(self):
        pass

    def draw(self):
        with self._shader.use():
            self._hex.draw()


class SlowTower(Tower):
    COST = 50
    _COLOUR = Colour(0.7, 0.5, 0.5)

    def __init__(self, app, level, tile):
        super().__init__(app, level, tile, SlowTower._COLOUR)
        self._level = level
        self._coords = Vector(tile.x, tile.y)

        for t in level.tile_neighbours(tile):
            t.slow = True


class KillTower(Tower):
    COST = 200
    _COOLDOWN = 10
    _COLOUR = Colour(0.5, 0.7, 0.5)

    def __init__(self, app, level, tile):
        super().__init__(app, level, tile, KillTower._COLOUR)
        self._level = level
        self._tile = tile
        self._coords = Vector(tile.x, tile.y)
        self._last_fire = 0

    def update(self):
        if self._level.timer.time > self._last_fire + KillTower._COOLDOWN:
            neighbours = self._level.tile_neighbours(self._tile)
            candidates = [e for e in self._level.enemies
                          if e.current_tile in neighbours]
            if len(candidates) > 0:
                candidates[0].kill()
                self._last_fire = self._level.timer.time


class MoneyTower(Tower):
    COST = 100
    _COOLDOWN = 6
    _COLOUR = Colour(0.5, 0.5, 0.7)
    _VALUE_INCREASE = 10
    def __init__(self, app, level, tile):
        super().__init__(app, level, tile, MoneyTower._COLOUR)
        self._level = level
        self._tile = tile
        self._coords = Vector(tile.x, tile.y)
        self._last_fire = 0

    def update(self):
        if self._level.timer.time > self._last_fire + MoneyTower._COOLDOWN:
            neighbours = self._level.tile_neighbours(self._tile)
            candidates = [e for e in self._level.enemies
                          if e.current_tile in neighbours]
            if len(candidates) > 0:
                candidates[0].value += MoneyTower._VALUE_INCREASE

# Tower ideas:
# Weaken tower (removes letters or words/phrases for multi-phrase enemies)
# Upgraded towers?
