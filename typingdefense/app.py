import sdl2.ext
import gamemenu
from .mainmenu import MainMenuScreen

class App(object):
    def __init__(self):
        """Initialize the App."""
        sdl2.ext.init()
        self._window = sdl2.ext.Window("Typing Defense",
                                       size=(800, 600),
                                       flags=sdl2.SDL_WINDOW_OPENGL)
        self._menu = gamemenu.Menu(MainMenuScreen())

    def __del__(self):
        sdl2.ext.quit()

    def run(self):
        """Run the App."""
        self._window.show()

        run = True
        while run:
            for event in sdl2.ext.get_events():
                if event.type == sdl2.SDL_QUIT:
                    run = False
                    break

            self._window.refresh()
