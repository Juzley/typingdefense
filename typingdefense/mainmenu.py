"""The main Typing Defense menu."""

from typingdefense.menu import MenuScreen

class MainMenuScreen(MenuScreen):
    def __init__(self, app):
        super(MainMenuScreen, self).__init__(app, "placeholder.png")
