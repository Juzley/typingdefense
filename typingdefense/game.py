"""Typing Defense - Game Module"""
from typingdefense.camera import Camera
from typingdefense.level import Level


class Game(object):
    def __init__(self, app):
        self.cam = Camera(
            origin=[0, 0, 10], target=[0, 0.1, 0], up=[0, 0, 1], fov=75,
            screen_width=app.window_width, screen_height=app.window_height,
            near=0.1, far=1000)
        self._level = Level(app, self)

    def draw(self):
        self._level.draw()
