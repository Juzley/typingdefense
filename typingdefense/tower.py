"""Module containing the different towers that can be placed by the player."""
import OpenGL.GL as GL
from .glutils import Hex, ShaderInstance
from .vector import Vector
from .util import Colour


class Tower(object):
    def __init__(self, app, level, tile):
        self._shader = ShaderInstance(
            app, 'level.vs', 'level.fs',
            [('transMatrix', GL.GL_FLOAT_MAT4,
              level.cam.trans_matrix_as_array()),
             ('colourIn', GL.GL_FLOAT_VEC4, Colour(0.5, 0.5, 0.5, 1))])
        self._hex = Hex(Vector(tile.x, tile.y, tile.top), 0.5, 2, stacks=4)

    def update(self, timer):
        pass

    def draw(self):
        with self._shader.use():
            self._hex.draw()

class SlowTower(Tower):
    COST = 50
    def __init__(self, app, level, tile):
        super().__init__(app, level, tile)
        self._level = level
        self._targets = []
        self._coords = Vector(tile.x, tile.y)

        for t in level.tile_neighbours(tile):
            t.slow = True

    def update(self, timer):
        super().update(timer)

    def draw(self):
        super().draw()

# Tower ideas:
# Slow tower
# Kill tower (kills an enemy)
# Weaken tower (removes letters or words/phrases for multi-phrase enemies)
# Money tower (makes enemies more valuable if killed in their range?)
# Upgraded towers?
