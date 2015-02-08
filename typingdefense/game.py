"""Typing Defense - Game Module"""
from typingdefense.camera import Camera
from typingdefense.level import Level
from typingdefense.hud import Hud


class Game(object):
    def __init__(self, app):
        self.cam = Camera(
            origin=[0, -10, 40], target=[0, 0, 0], up=[0, 1, 0], fov=45,
            screen_width=app.window_width, screen_height=app.window_height,
            near=0.1, far=1000)
        self._level = Level(app, self)
        self._hud = Hud(app)

    def draw(self):
        self._level.draw()
        self._hud.draw()
