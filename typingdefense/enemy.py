"""Module containing the different enemies that appear in the game."""
import sys
import math
import numpy
from OpenGL import GL
from .phrase import Phrase
from .vector import Vector
from .glutils import ShaderInstance, Hex
from .util import Transform, Colour
from .phrasebook import PhraseBook


# List of enemy types
enemy_types = []


class _EnemyMeta(type):
    """Metatype used to build the collection of enemy types."""
    def __init__(cls, name, bases, attrs):
        if cls not in enemy_types:
            enemy_types.append(cls)


class _BaseEnemy(object):
    """Base class for all enemy types."""
    _JUMP_HEIGHT = 3
    _SLOW_FACTOR = 1.5

    def __init__(self, app, level, tile, speed, move_pause, value, damage,
                 colour, health=1, words=1, wordlength=PhraseBook.SHORT_PHRASE):
        self._app = app
        self._level = level
        self._tile = tile

        # Phrase variables
        self._words = words
        self._wordlength = wordlength
        self.phrase = None

        # Movement variables
        self.origin = Vector(tile.x, tile.y, tile.top)
        self.prev_tile = None
        self.current_tile = tile
        self.next_tile = tile.path_next
        self._speed = speed
        self._move_pause = move_pause
        self._start_pos = None
        self._end_pos = None
        self._move_start = 0
        self._move_end = 0

        # Graphics variables
        self._shader = ShaderInstance(
            app, 'level.vs', 'level.fs',
            [('transMatrix', GL.GL_FLOAT_MAT4, None),
             ('colourIn', GL.GL_FLOAT_VEC4, colour)])
        self._hex = Hex(Vector(0, 0, 0), 0.5, 1)

        self.health = health
        self.damage = damage
        self.unlink = False
        self.value = value

        # Initial setup
        self._setup_move(level.timer)
        self._setup_phrase()

    def _scaled_speed(self):
        if self.current_tile.slow:
            return self._speed * _BaseEnemy._SLOW_FACTOR
        else:
            return self._speed

    def _scaled_pause(self):
        if self.current_tile.slow:
            return self._move_pause / _BaseEnemy._SLOW_FACTOR
        else:
            return self._move_pause

    def _die(self):
        self._level.money += self.value
        self._level.phrases.release_start_letter(self.phrase.start)
        self.unlink = True

    def _setup_phrase(self):
        self.phrase = Phrase(self._app, self._level.cam,
                             self._level.phrases.get_phrase(self._wordlength,
                                                            self._words))

    def _setup_move(self, timer):
        if self.next_tile:
            self._start_pos = Vector(self.current_tile.x,
                                     self.current_tile.y,
                                     self.current_tile.top)
            self._end_pos = Vector(self.next_tile.x,
                                   self.next_tile.y,
                                   self.next_tile.top)
            distance = (self._end_pos - self._start_pos).magnitude

            self._move_start = timer.time + self._scaled_pause()
            self._move_end = self._move_start + distance / self._scaled_speed()

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
            self.health -= 1
            if self.health <= 0:
                self._die()
            else:
                self._setup_phrase()

    def kill(self):
        self._die()

    def update(self, timer):
        if timer.time >= self._move_start:
            progress = ((timer.time - self._move_start) /
                        (self._move_end - self._move_start))
            self.origin = self._start_pos + ((self._end_pos - self._start_pos) *
                                             progress)
            self.origin.z += _BaseEnemy._JUMP_HEIGHT * math.sin(progress *
                                                                math.pi)

        if timer.time >= self._move_end:
            if self.next_tile:
                self.prev_tile = self.current_tile
                self.current_tile = self.next_tile
                self.next_tile = self.next_tile.path_next
                self._setup_move(timer)

            if self.current_tile == self._level.base.tile:
                self._level.base.damage(self.damage)
                self.unlink = True

                if self.unlink:
                    self._level.phrases.release_start_letter(self.phrase.start)


class BasicEnemy(_BaseEnemy, metaclass=_EnemyMeta):
    _SPEED = 6
    _MOVE_PAUSE = 1.5
    _DAMAGE = 20
    _VALUE = 50

    def __init__(self, app, level, tile):
        super().__init__(app, level, tile,
                         speed=BasicEnemy._SPEED,
                         move_pause=BasicEnemy._MOVE_PAUSE,
                         value=BasicEnemy._VALUE,
                         damage=BasicEnemy._DAMAGE,
                         colour=Colour.from_red())

class AccelEnemy(_BaseEnemy, metaclass=_EnemyMeta):
    pass


class Wave(object):
    def __init__(self, app, level, tile,
                 enemy_count=10, start_time=0, spawn_gap=5,
                 enemy_type=BasicEnemy):
        self.tile = tile
        self._app = app
        self._level = level
        self._last_spawn = 0
        self._spawn_count = 0

        # To make level saving/loading easier, allow enemy-type to be passed
        # in as a string. Convert to a class here.
        if type(enemy_type) == str:
            enemy_type = getattr(sys.modules[__name__], enemy_type)

        self.enemy_type = enemy_type
        self.enemy_count = enemy_count
        self.start_time = start_time
        self.spawn_gap  = spawn_gap

    def update(self, timer):
        if (timer.time >= self.start_time and
                timer.time - self._last_spawn > self.spawn_gap and
                not self.finished):
            self._level.add_enemy(
                self.enemy_type(self._app, self._level, self.tile))
            self._last_spawn = timer.time
            self._spawn_count += 1

    @property
    def finished(self):
        return self._spawn_count == self.enemy_count
