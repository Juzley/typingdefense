"""Typing Defense - Game Module"""
from typingdefense.camera import Camera
from typingdefense.level import Level
from typingdefense.hud import Hud


class Game(object):
    def __init__(self, app):
        # TODO: Move cam to level
        self.cam = Camera(
            origin=[0, -10, 40], target=[0, 0, 0], up=[0, 1, 0], fov=45,
            screen_width=app.window_width, screen_height=app.window_height,
            near=0.1, far=1000)
        self._level = Level(app, self)

    def draw(self):
        self._level.draw()

    def update(self):
        self._level.update()

    def on_click(self, x, y):
        self._level.on_click(x, y)

    def on_keydown(self, key):
        self._level.on_keydown(key)

    def on_text(self, c):
        self._level.on_text(c)
