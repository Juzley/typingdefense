import sdl2
import sdl2.ext
from OpenGL import GL
from .menu import Menu
from .mainmenu import MainMenuScreen
from .resources import Resources
from .game import Game


class App(object):
    def __init__(self):
        """Initialize the App."""
        sdl2.ext.init()

        self.resources = Resources(resource_path="resources",
                                   texture_path="textures",
                                   shader_path="shaders",
                                   font_path="fonts")

        self.window_width = 800
        self.window_height = 600
        self._window = sdl2.ext.Window("Typing Defense",
                                       size=(self.window_width,
                                             self.window_height),
                                       flags=sdl2.SDL_WINDOW_OPENGL)
        self._gl_context = None
        self._init_gl()

        self._menu = Menu(MainMenuScreen(self))
        self._game = Game(self)

    def __del__(self):
        """Shut down the App."""
        sdl2.SDL_GL_DeleteContext(self._gl_context)
        sdl2.ext.quit()

    def _init_gl(self):
        """Set up OpenGL."""
        sdl2.video.SDL_GL_SetAttribute(
            sdl2.video.SDL_GL_CONTEXT_MAJOR_VERSION, 3)
        sdl2.video.SDL_GL_SetAttribute(
            sdl2.video.SDL_GL_CONTEXT_MINOR_VERSION, 1)
        sdl2.video.SDL_GL_SetAttribute(
            sdl2.video.SDL_GL_CONTEXT_PROFILE_MASK,
            sdl2.video.SDL_GL_CONTEXT_PROFILE_CORE)
        sdl2.video.SDL_GL_SetAttribute(
            sdl2.video.SDL_GL_DOUBLEBUFFER, 1)
        self._gl_context = sdl2.SDL_GL_CreateContext(self._window.window)

        GL.glClearColor(0, 0, 0, 1)

        GL.glEnable(GL.GL_BLEND)
        GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)

        GL.glEnable(GL.GL_CULL_FACE)
        GL.glCullFace(GL.GL_BACK)

    def _draw(self):
        """Draw the next frame."""
        GL.glClear(GL.GL_STENCIL_BUFFER_BIT |
                   GL.GL_DEPTH_BUFFER_BIT |
                   GL.GL_COLOR_BUFFER_BIT)
        # self._menu.draw()
        self._game.draw()
        sdl2.SDL_GL_SwapWindow(self._window.window)

    def _update(self):
        """Perform any updates needed in this frame."""
        self._game.update()

    def run(self):
        """Run the App."""
        self._window.show()

        run = True
        while run:
            for event in sdl2.ext.get_events():
                if event.type == sdl2.SDL_QUIT:
                    run = False
                    break
                elif event.type == sdl2.SDL_MOUSEBUTTONDOWN:
                    self._game.on_click(event.button.x,
                                        self.window_height - event.button.y,
                                        event.button.button)
                elif event.type == sdl2.SDL_TEXTINPUT:
                    for c in event.text.text:
                        self._game.on_text(chr(c))
                elif event.type == sdl2.SDL_KEYDOWN:
                    self._game.on_keydown(event.key.keysym.sym)

            self._update()
            self._draw()
