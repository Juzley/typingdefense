"""Module containing the different enemies that appear in the game."""
import numpy
from OpenGL import GL
from .phrase import Phrase
from .vector import Vector
from .glutils import ShaderInstance, Hex
from .util import Transform


class Enemy(object):
    SPEED = 1
    DAMAGE = 20

    def __init__(self, app, level, tile):
        self.origin = Vector(tile.x, tile.y, tile.top)
        self.phrase = Phrase(app, level.cam, "PHRASE")

        self._level = level
        self._current_tile = tile
        self._next_tile = tile.path_next

        self._move_start = 0
        self._move_end = 0
        self._move_dir = None
        self._setup_move(level.timer)

        self.unlink = False

        self._shader = ShaderInstance(
            app, 'level.vs', 'level.fs',
            [('transMatrix', GL.GL_FLOAT_MAT4, None),
             ('colourIn', GL.GL_FLOAT_VEC4, [1, 0, 0, 1])])
        self._hex = Hex(Vector(0, 0, 0), 0.5, 1)

    def draw(self):
        coords = Vector(self.origin.x, self.origin.y, self.origin.z)
        self.phrase.draw(coords)

        t = Transform(coords)
        m = self._level.cam.trans_matrix * t.matrix
        self._shader.set_uniform('transMatrix',
                                 numpy.asarray(m).reshape(-1),
                                 download=False)
        with self._shader.use():
            self._hex.draw()

    def on_text(self, c):
        self.phrase.on_type(c)
        self.unlink = self.phrase.complete

    def update(self, timer):
        self.origin += self._move_dir * timer.frametime * Enemy.SPEED

        if timer.time >= self._move_end:
            if self._next_tile:
                self._current_tile = self._next_tile
                self._next_tile = self._next_tile.path_next
                self._setup_move(timer)

            if self._current_tile == self._level.base.tile:
                self._level.base.damage(Enemy.DAMAGE)
                self.unlink = True

    def _setup_move(self, timer):
        if self._next_tile:
            start = Vector(self._current_tile.x,
                           self._current_tile.y,
                           self._current_tile.top)
            end = Vector(self._next_tile.x,
                         self._next_tile.y,
                         self._next_tile.top)
            distance = (end - start).magnitude

            self._move_dir = (end - start)
            self._move_dir.normalize()

            self._move_start = timer.time
            self._move_end = self._move_start + distance / Enemy.SPEED
        else:
            self._move_dir = Vector(0, 0)


class Wave(object):
    def __init__(self, app, level, tile):
        self.tile = tile
        self._app = app
        self._level = level
        self._start_time = 1
        self._spawn_pause = 1
        self._last_spawn = 0
        self._spawn_count = 0
        self._spawn_target = 10

    def update(self, timer):
        if (timer.time >= self._start_time and
                timer.time - self._last_spawn > self._spawn_pause and
                not self.finished):
            self._level.add_enemy(Enemy(self._app, self._level, self.tile))
            self._last_spawn = timer.time
            self._spawn_count += 1

    @property
    def finished(self):
        return self._spawn_count == self._spawn_target
