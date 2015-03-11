"""Typing Defense - Game Module"""
import sdl2
import typingdefense.level as level
import typingdefense.editor as editor


class Game(object):
    def __init__(self, app):
        self._app = app
        self._level = level.Level(app, self)

    def draw(self):
        self._level.draw()

    def update(self):
        self._level.update()

    def on_click(self, x, y, button):
        self._level.on_click(x, y, button)

    def on_keydown(self, key):
        if key == sdl2.SDLK_F12:
            self._level = editor.Editor(self._app, self._level)

        self._level.on_keydown(key)

    def on_text(self, c):
        self._level.on_text(c)
