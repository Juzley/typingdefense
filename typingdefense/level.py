import math
import numpy
from OpenGL import GL
import typingdefense.glutils as glutils


class TilePickingShader(object):
    def __init__(self, app):
        self._shader = app.resources.load_shader_program('level.vs',
                                                         'picking.fs')
        self._transmatrix_uniform = self._shader.uniform('transMatrix')
        self._colour_uniform = self._shader.uniform('colourIn')

    def use(self):
        self._shader.use()

    def set_coords(self, q, r):
        GL.glUniform4f(self._colour_uniform, q, r, 0, 0)

    def set_transmatrix(self, mat):
        GL.glUniformMatrix4fv(self._transmatrix_uniform, 1, GL.GL_TRUE,
                              mat)


class Tile(object):
    """Class representing a single tile in a level."""
    SIZE = 1
    DEPTH = 1
    HEIGHT = SIZE * 2
    WIDTH = SIZE * (math.sqrt(3)/2) * HEIGHT
    VERT_SPACING = HEIGHT * 0.75
    HORIZ_SPACING = WIDTH

    def __init__(self, app, cam, q, r, height):
        """Construct a (hexagonal) tile.

        p and q are the horizontal coordinates of the tile (using axial
        coordinates).
        height is the number of stacks in the tile.
        """
        self._cam = cam
        self.q = q
        self.r = r
        self.height = height

        self._vao = None
        self._vbo = None
        self._setup_vert_buffers()

        self._shader = None
        self._transmatrix_uniform = 0
        self._colour_uniform = 0
        self._setup_shader(app.resources)

    def _setup_vert_buffers(self):
        """Populate the vertex buffers for the tile."""
        x, y = self.world_location()
        z = 0

        # The top layer of the tile is drawn with a line loop.
        # The vertical sections are drawn with lines.
        top_verts, vert_verts = ([], [])
        for i in range(6):
            px = x + Tile.SIZE * math.sin((2 * math.pi / 6) * i)
            py = y + Tile.SIZE * math.cos((2 * math.pi / 6) * i)
            top_verts.extend([px, py, z + Tile.DEPTH])
            vert_verts.extend([px, py, z, px, py, z + Tile.DEPTH])

        # Put all the points into the same vertex buffer: top then mid.
        verts = numpy.array(top_verts + vert_verts, numpy.float32)

        self._vao = glutils.VertexArray()
        self._vbo = glutils.VertexBuffer()
        with self._vao.bind():
            self._vbo.bind()
            GL.glBufferData(GL.GL_ARRAY_BUFFER, verts.nbytes, verts,
                            GL.GL_STATIC_DRAW)
            GL.glEnableVertexAttribArray(0)
            GL.glVertexAttribPointer(0, 3, GL.GL_FLOAT, GL.GL_FALSE, 0, None)

    def _setup_shader(self, resources):
        """Load the shader program for the tile."""
        self._shader = resources.load_shader_program("level.vs",
                                                     "level.fs")
        self._transmatrix_uniform = self._shader.uniform('transMatrix')
        self._colour_uniform = self._shader.uniform('colourIn')

    def world_location(self):
        """Determine the location in world coordinates of the tile center."""
        x = Tile.SIZE * math.sqrt(3) * (self.q + self.r / 2)
        y = Tile.SIZE * (3 / 2) * self.r
        return (x, y)

    def draw(self):
        """Draw the tile."""
        self._shader.use()
        GL.glUniformMatrix4fv(self._transmatrix_uniform, 1, GL.GL_TRUE,
                              self._cam.trans_matrix_as_array())
        GL.glUniform4f(self._colour_uniform, 1.0, 1.0, 1.0, 1.0)

        with self._vao.bind(), glutils.linewidth(3):
            GL.glDrawArrays(GL.GL_TRIANGLE_FAN, 0, 6)
            GL.glUniform4f(self._colour_uniform, 0.0, 1.0, 0.0, 1.0)
            GL.glDrawArrays(GL.GL_LINE_LOOP, 0, 6)
            GL.glDrawArrays(GL.GL_LINE_LOOP, 6, 6)
            GL.glDrawArrays(GL.GL_LINES, 12, 12)

        GL.glUseProgram(0)

    def picking_draw(self, picking_shader):
        """Draw to the picking framebuffer.

        This allows us to determine which tile was hit by mouse events.
        """
        picking_shader.set_transmatrix(self._cam.trans_matrix_as_array())
        picking_shader.set_coords(self.q, self.r)
        with self._vao.bind(), glutils.linewidth(3):
            GL.glDrawArrays(GL.GL_TRIANGLE_FAN, 0, 6)
            GL.glDrawArrays(GL.GL_LINE_LOOP, 0, 6)
            GL.glDrawArrays(GL.GL_LINE_LOOP, 6, 6)
            GL.glDrawArrays(GL.GL_LINES, 12, 12)


class Base(object):
    """Class representing the player's base."""
    def __init__(self, app, cam, x, y, z):
        self._cam = cam

        top_verts, mid_verts, bottom_verts = ([], [], [])
        for i in range(6):
            px = x + math.sin((2 * math.pi / 6) * i)
            py = y + Tile.SIZE * math.cos((2 * math.pi / 6) * i)
            top_verts.extend([px, py, z + 1])
            bottom_verts.extend([px, py, z])
            mid_verts.extend([px, py, z, px, py, z + 1])

        # Put all the points into the same vertex buffer: top, bottom then mid.
        verts = numpy.array(top_verts + bottom_verts + mid_verts, numpy.float32)

        self._vao = GL.glGenVertexArrays(1)
        self._vbo = GL.glGenBuffers(1)
        GL.glBindVertexArray(self._vao)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self._vbo)
        GL.glBufferData(GL.GL_ARRAY_BUFFER, verts.nbytes, verts,
                        GL.GL_STATIC_DRAW)
        GL.glEnableVertexAttribArray(0)
        GL.glVertexAttribPointer(0, 3, GL.GL_FLOAT, GL.GL_FALSE, 0, None)
        GL.glBindVertexArray(0)

        self._shader = app.resources.load_shader_program("level.vs",
                                                         "level.fs")
        self._transmatrix_uniform = self._shader.uniform('transMatrix')
        self._colour_uniform = self._shader.uniform('colourIn')

    def draw(self):
        self._shader.use()
        GL.glUniformMatrix4fv(self._transmatrix_uniform, 1, GL.GL_TRUE,
                              self._cam.trans_matrix_as_array())
        GL.glUniform4f(self._colour_uniform, 1.0, 0.0, 0.0, 1.0)

        GL.glBindVertexArray(self._vao)
        GL.glDrawArrays(GL.GL_TRIANGLE_FAN, 0, 6)
        GL.glLineWidth(3)
        GL.glDrawArrays(GL.GL_LINE_LOOP, 0, 6)
        GL.glDrawArrays(GL.GL_LINE_LOOP, 6, 6)

        GL.glDrawArrays(GL.GL_LINES, 12, 12)
        GL.glLineWidth(1)
        GL.glBindVertexArray(0)

        GL.glUseProgram(0)


class Level(object):
    """Class representing a game level."""
    def __init__(self, app, game):
        self._cam = game.cam
        self._vao = GL.glGenVertexArrays(1)
        self._vbo = GL.glGenBuffers(1)

        # TODO: Consider whether this should be in Tile or not.
        # Maybe move tile drawing etc to level class?
        self._shader = app.resources.load_shader_program("level.vs",
                                                         "level.fs")
        self._transmatrix_uniform = self._shader.uniform('transMatrix')

        self._picking_texture = glutils.PickingTexture(app.window_width,
                                                       app.window_height)
        self._picking_shader = TilePickingShader(app)

        self._min_p, self._max_p = (0, 0)
        self._min_r, self._max_r = (0, 0)
        self._tiles = None
        self._base = None
        self.load(app)

    def load(self, app):
        self._min_p = -2
        self._max_p = 2
        self._min_r = 0
        self._max_r = 2

        self._tiles = numpy.matrix(
            [[None, None, Tile(app, self._cam, 0, 0, 0), Tile(app, self._cam, 1, 0, 0), Tile(app, self._cam, 2, 0, 0)],
             [None, Tile(app, self._cam, -1, 1, 0), Tile(app, self._cam, 0, 1, 0), Tile(app, self._cam, 1, 1, 0), Tile(app, self._cam, 2, 1, 0)],
             [None, Tile(app, self._cam, -1, 2, 0), Tile(app, self._cam, 0, 2, 0), Tile(app, self._cam, 1, 2, 0), None],
             [Tile(app, self._cam, -2, 3, 0), Tile(app, self._cam, -1, 3, 0), Tile(app, self._cam, 0, 3, 0), Tile(app, self._cam, 1, 3, 0), None]])
        self._base = Base(app, self._cam, 0, 0, Tile.HEIGHT)

    def draw(self):
        # Do the picking draw first.
        with self._picking_texture.enable():
            GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
            self._picking_shader.use()
            for _, tile in numpy.ndenumerate(self._tiles):
                if tile:
                    tile.picking_draw(self._picking_shader)
            GL.glUseProgram(0)

        # Now actually draw the tiles
        for _, tile in numpy.ndenumerate(self._tiles):
            if tile:
                tile.draw()
        self._base.draw()

        GL.glUseProgram(0)

    def on_click(self, x, y):
        print(self._picking_texture.read(x, y))
