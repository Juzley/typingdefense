from OpenGL import GL
import numpy


class MenuItem(object):
    pass


class TextButtonItem(MenuItem):
    def __init__(self, x, y, h, text):
        self.x, self.y, self.h = (x, y, h)
        self.text = text
        self.selected = False

    def draw(self):
        pass


class MenuScreen(object):
    def __init__(self, app, background=None, items=None):
        self._background = background

        if items is None:
            self._items = []
        else:
            self._items = items

        # Load the background image info.
        if self._background:
            app.resources.load_texture(self._background)
            self._bg_shader = app.resources.load_shader_program("test.vs",
                                                                "test.fs")
            self._bg_vao = GL.glGenVertexArrays(1)
            GL.glBindVertexArray(self._bg_vao)
            self._bg_vbo = GL.glGenBuffers(1)
            GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self._bg_vbo)
            verts = numpy.array(
                [-1.0, -1.0, 0.0,
                 -1.0, 1.0, 0.0,
                 1.0, -1.0, 0.0,
                 1.0, 1.0, 0.0],
                dtype=numpy.float32)
            GL.glBufferData(GL.GL_ARRAY_BUFFER, verts.nbytes, verts,
                            GL.GL_STATIC_DRAW)
            GL.glEnableVertexAttribArray(0)
            GL.glVertexAttribPointer(0, 3, GL.GL_FLOAT, GL.GL_FALSE, 0, None)
            GL.glBindVertexArray(0)

            GL.glBindVertexArray(0)

    def __del__(self):
        # TODO: release VAO etc?
        pass

    def draw(self):
        if self._background:
            GL.glUseProgram(self._bg_shader.program)
            GL.glBindVertexArray(self._bg_vao)
            GL.glDrawArrays(GL.GL_TRIANGLE_STRIP, 0, 4)
            GL.glBindVertexArray(0)


class Menu(object):

    """Menu class.

    Manages a number of menu screens and coordinates moving between them.
    """

    def __init__(self, start_screen):
        """Initialize a menu."""
        self._menu_stack = []
        self.reset(start_screen)

    def draw(self):
        """Draw the menu."""
        self._menu_stack[-1].draw()

    def reset(self, screen):
        """Reset the menu.

        This discards the current menu stack and starts again at the given
        screen.
        """
        self._menu_stack = [screen]

    def navigate_forward(self, screen):
        """Move to a new screen.

        The current screen is kept on the stack so we can go back to it.
        """
        self._menu_stack.append(screen)

    def navigate_back(self):
        """Move to the previous screen."""
        self._menu_stack.pop()
