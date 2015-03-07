"""Module containing the different enemies that appear in the game."""
import math
import numpy
from OpenGL import GL
from .phrase import Phrase
from .vector import Vector
from .glutils import ShaderInstance, Hex
from .util import Transform
from .phrasebook import PhraseBook


class Enemy(object):
    _SPEED = 6
    _MOVE_PAUSE = 1.5
    _SLOW_FACTOR = 0.5
    _DAMAGE = 20
    _JUMP_HEIGHT = 3
    _START_REWARD = 100

    def __init__(self, app, level, tile):
        self.origin = Vector(tile.x, tile.y, tile.top)
        self.phrase = Phrase(app, level.cam,
                             level.phrases.get_word(PhraseBook.SHORT_PHRASE))
        self.slowed = False

        self._level = level
        self.current_tile = tile
        self._next_tile = tile.path_next

        self._start_pos = None
        self._end_pos = None
        self._move_start = 0
        self._move_end = 0
        self._setup_move(level.timer)

        self.unlink = False

        self.value = Enemy._START_REWARD

        self._shader = ShaderInstance(
            app, 'level.vs', 'level.fs',
            [('transMatrix', GL.GL_FLOAT_MAT4, None),
             ('colourIn', GL.GL_FLOAT_VEC4, [1, 0, 0, 1])])
        self._hex = Hex(Vector(0, 0, 0), 0.5, 1)

    def _scaled_speed(self):
        if self.current_tile.slow:
            return Enemy._SPEED * Enemy._SLOW_FACTOR
        else:
            return Enemy._SPEED

    def _scaled_pause(self):
        if self.current_tile.slow:
            return Enemy._MOVE_PAUSE / Enemy._SLOW_FACTOR
        else:
            return Enemy._MOVE_PAUSE

    def draw(self):
        coords = Vector(self.origin.x, self.origin.y, self.origin.z)
        t = Transform(coords)
        m = self._level.cam.trans_matrix * t.matrix
        self._shader.set_uniform('transMatrix',
                                 numpy.asarray(m).reshape(-1),
                                 download=False)
        with self._shader.use():
            self._hex.draw()

        self.phrase.draw(coords)

    def on_text(self, c):
        self.phrase.on_type(c)

        if self.phrase.complete:
            self._level.money += self.value
            self._level.phrases.release_start_letter(self.phrase.start)
            self.unlink = True

    def kill(self):
        self._level.phrases.release_start_letter(self.phrase.start)
        self.unlink = True

    def update(self, timer):
        if timer.time >= self._move_start:
            progress = ((timer.time - self._move_start) /
                        (self._move_end - self._move_start))
            self.origin = self._start_pos + ((self._end_pos - self._start_pos) *
                                             progress)
            self.origin.z += Enemy._JUMP_HEIGHT * math.sin(progress * math.pi)

        if timer.time >= self._move_end:
            if self._next_tile:
                self.current_tile = self._next_tile
                self._next_tile = self._next_tile.path_next
                self._setup_move(timer)

            if self.current_tile == self._level.base.tile:
                self._level.base.damage(Enemy._DAMAGE)
                self.unlink = True

                if self.unlink:
                    self._level.phrases.release_start_letter(self.phrase.start)

    def _setup_move(self, timer):
        if self._next_tile:
            self._start_pos = Vector(self.current_tile.x,
                                     self.current_tile.y,
                                     self.current_tile.top)
            self._end_pos = Vector(self._next_tile.x,
                                   self._next_tile.y,
                                   self._next_tile.top)
            distance = (self._end_pos - self._start_pos).magnitude

            self._move_start = timer.time + self._scaled_pause()
            self._move_end = self._move_start + distance / self._scaled_speed()


class Wave(object):
    def __init__(self, app, level, tile):
        self.tile = tile
        self._app = app
        self._level = level
        self._start_time = 1
        self._spawn_pause = 5
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
