"""Module containing the different enemies that appear in the game."""
from .phrase import Phrase
from .vector import Vector


class Enemy(object):
    SPEED = 1

    def __init__(self, app, cam, timer, tile):
        self.origin = Vector(tile.x, tile.y)
        self.phrase = Phrase(app, cam, "PHRASE")

        self._current_tile = tile
        self._next_tile = tile.path_next

        self._move_start = 0
        self._move_end = 0
        self._move_dir = None
        self._setup_move(timer)

    def draw(self):
        self.phrase.draw(Vector(self.origin.x, self.origin.y, 0))

    def on_text(self, c):
        self.phrase.on_type(c)

    def unlink(self):
        return self.phrase.complete

    def update(self, timer):
        self.origin += self._move_dir * timer.frametime * Enemy.SPEED

        if timer.time >= self._move_end:
            if self._next_tile:
                self._current_tile = self._next_tile
                self._next_tile = self._next_tile.path_next
                self._setup_move(timer)

    def _setup_move(self, timer):
        if self._next_tile:
            start = Vector(self._current_tile.x, self._current_tile.y)
            end = Vector(self._next_tile.x, self._next_tile.y)
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
            self._level.add_enemy(Enemy(self._app, self._level.cam, timer,
                                        self._tile))
            self._last_spawn = timer.time
            self._spawn_count += 1

    @property
    def finished(self):
        return self._spawn_count == self._spawn_target
