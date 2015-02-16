"""Module containing all classes required to represent and handle a level."""
import math
import numpy
import weakref
import sdl2
import json
from collections import deque
from enum import Enum, unique
from OpenGL import GL
import typingdefense.glutils as glutils
from typingdefense.vector import Vector
from typingdefense.enemy import Enemy
from typingdefense.util import Timer
from typingdefense.hud import Hud


def _cube_round(fc):
    """Round fractional cube-format hex coordinates."""
    rx = round(fc.x)
    ry = round(fc.y)
    rz = round(fc.z)

    x_diff = abs(rx - fc.x)
    y_diff = abs(ry - fc.y)
    z_diff = abs(rz - fc.z)

    if x_diff > y_diff and x_diff > z_diff:
        rx = -ry - rz
    elif y_diff > z_diff:
        ry = -rx - rz
    else:
        rz = -rx - ry

    return Vector(rx, ry, rz)


def _hex_round(fh):
    """Round fractional axial-format hex coordinates."""
    return _cube_to_hex(_cube_round(_hex_to_cube(fh)))


def _hex_to_cube(h):
    """Convert axial-format hex coordinates to cube-format."""
    return Vector(h.q, -h.q - h.r, h.r)


def _cube_to_hex(c):
    """Convert cube-format hex coordinates to hex."""
    return Vector(c.x, c.z)


class Tile(object):
    """Class representing a single tile in a level."""
    SIZE = 1
    DEPTH = 1
    HEIGHT = SIZE * 2
    WIDTH = SIZE * (math.sqrt(3)/2) * HEIGHT
    VERT_SPACING = HEIGHT * 0.75
    HORIZ_SPACING = WIDTH

    def __init__(self, app, cam, coords, height):
        """Construct a (hexagonal) tile.

        coords is a vector containing the horizontal coordinates of the tile,
        using axial coordinates.
        height is the number of stacks in the tile.
        """
        self._cam = cam
        self.coords = coords
        self.height = height
        self.path_next = None

        self._vao = None
        self._vbo = None
        self._setup_vert_buffers()

        self._shader = None
        self._transmatrix_uniform = 0
        self._colour_uniform = 0
        self._setup_shader(app.resources)

    def _setup_vert_buffers(self):
        """Populate the vertex buffers for the tile."""
        z = 0

        # The top layer of the tile is drawn with a line loop.
        # The vertical sections are drawn with lines.
        top_verts, vert_verts = ([], [])
        for i in range(6):
            px = self.x + Tile.SIZE * math.sin((2 * math.pi / 6) * i)
            py = self.y + Tile.SIZE * math.cos((2 * math.pi / 6) * i)
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

    @property
    def q(self):
        """The axial q coord of the tile."""
        return self.coords.q

    @property
    def r(self):
        """The axial r coord of the tile."""
        return self.coords.r

    @property
    def x(self):
        """Calculate the x value of the world location of the tile center."""
        return Tile.SIZE * math.sqrt(3) * (self.q + self.r / 2)

    @property
    def y(self):
        """Calculate the y value of the world location of the tile center."""
        return Tile.SIZE * (3 / 2) * self.r

    @staticmethod
    def world_to_tile_coords(world_coords):
        """Convert world (x, y) coordinates to tile (q, r) coordinates.

        Note that this is a 2D conversion only."""
        # TODO: is this in the right place?
        q = (world_coords.x * math.sqrt(3) / 3 - world_coords.y / 3) / Tile.SIZE
        r = (world_coords.y * 2 / 3) / Tile.SIZE
        return _hex_round(Vector(q, r))

    @property
    def empty(self):
        # TODO
        return True

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
        picking_shader.set_uniform('colourIn',
                                   [self.coords.q, self.coords.r, 0, 0])
        with self._vao.bind(), glutils.linewidth(3):
            GL.glDrawArrays(GL.GL_TRIANGLE_FAN, 0, 6)
            GL.glDrawArrays(GL.GL_LINE_LOOP, 0, 6)
            GL.glDrawArrays(GL.GL_LINE_LOOP, 6, 6)
            GL.glDrawArrays(GL.GL_LINES, 12, 12)


class Base(object):
    """Class representing the player's base."""
    def __init__(self, app, cam, origin, z):
        self._cam = cam

        top_verts, mid_verts, bottom_verts = ([], [], [])
        for i in range(6):
            px = origin.x + math.sin((2 * math.pi / 6) * i)
            py = origin.y + Tile.SIZE * math.cos((2 * math.pi / 6) * i)
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
        """Draw the base."""
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

    @unique
    class State(Enum):
        """Enumeration of different level states."""
        defend = 1
        build = 2

    # TODO: cam should be part of level probably
    def __init__(self, app, game):
        self._app = app
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
        self._picking_shader = glutils.ShaderInstance(
            app, 'level.vs', 'picking.fs',
            [['transMatrix', GL.GL_FLOAT_MAT4,
              game.cam.trans_matrix_as_array()],
             ['colourIn', GL.GL_FLOAT_VEC4, [0, 0, 0, 0]]])

        # Level state
        self.timer = Timer()
        self.gold = 0
        self.state = Level.State.build
        self._target = None
        self._enemies = [Enemy(app, game.cam, Vector(0, 0, 1))]
        self._editing = False

        # Map/graphics etc.
        self._min_coords = None
        self._max_coords = None
        self._tiles = None
        self._base = None
        self.load(app)
        self._build_paths()

        self._hud = Hud(app, self)

    def load(self, app):
        """Load the level."""
        self._min_coords = Vector(-100, -100)
        self._max_coords = Vector(100, 100)

        width = self._max_coords.x - self._min_coords.x + 1
        height = self._max_coords.y - self._min_coords.y + 1
        self._tiles = numpy.empty([height, width], dtype=object)
        try:
            with open('resources/levels/test_level.tdl', 'r') as f:
                lvl_info = json.load(f)
                for tile_info in lvl_info['tiles']:
                    coords = Vector(tile_info['q'], tile_info['r'])
                    idx = self._tile_coords_to_array_index(coords)
                    self._tiles[idx.y, idx.x] = Tile(app,
                                                     self._cam,
                                                     coords,
                                                     tile_info['height'])
        except FileNotFoundError:
            pass

        self._base = Base(app, self._cam, Vector(0, 0), Tile.HEIGHT)

    def _save(self):
        """Save the edited level to file."""
        level = {}
        level['name'] = 'Test Level'

        tiles = []
        for _, tile in numpy.ndenumerate(self._tiles):
            if tile:
                tiles.append({'q': tile.q, 'r': tile.r, 'height': tile.height})
        level['tiles'] = tiles

        with open('resources/levels/test_level.tdl', 'w') as f:
            json.dump(level, f)

    def draw(self):
        """Draw the level."""
        self._hud.draw()

        # Do the picking draw first.
        with self._picking_texture.enable():
            with self._picking_shader.use():
                GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
                self._picking_shader.set_uniform('transMatrix')
                for _, tile in numpy.ndenumerate(self._tiles):
                    if tile:
                        tile.picking_draw(self._picking_shader)

        # Now actually draw the tiles
        for _, tile in numpy.ndenumerate(self._tiles):
            if tile:
                tile.draw()
        self._base.draw()
        GL.glUseProgram(0)

        for enemy in self._enemies:
            enemy.draw()

    def play(self):
        """Move from build into play state."""
        if self.state == Level.State.build:
            self.state = Level.State.defend

    def update(self):
        """Advance the game state."""
        self.timer.update()

        for enemy in self._enemies:
            enemy.update(self.timer)

        unlink_enemies = [e for e in self._enemies if e.unlink()]
        for enemy in unlink_enemies:
            self._enemies.remove(enemy)

    def on_click(self, x, y):
        """Handle a mouse click."""
        hit_hud = self._hud.on_click(x, y)

        if not hit_hud:
            if self._editing:
                # Work out if we hit an existing tile
                tile = self._screen_coords_to_tile(Vector(x, y))
                if not tile:
                    tile_coords = self._screen_coords_to_tile_coords(
                        Vector(x, y))
                    if self._tile_coords_valid(tile_coords):
                        index = self._tile_coords_to_array_index(tile_coords)
                        self._tiles[index.y, index.x] = Tile(self._app,
                                                             self._cam,
                                                             tile_coords, 0)
            else:
                tile = self._screen_coords_to_tile(Vector(x, y))
                if tile:
                    print("Tile: {},{}".format(tile.q, tile.r))
                    if tile.path_next:
                        print("    Next: {},{}".format(tile.path_next.q,
                                                       tile.path_next.r))

    def on_keydown(self, key):
        """Handle keydown events."""
        if key == sdl2.SDLK_F12:
            self._editing = not self._editing
        elif key == sdl2.SDLK_s:
            if self._editing:
                self._save()

    def on_text(self, c):
        """Handle text input."""
        self._update_target(c)
        if self._target and self._target():
            # TODO: Enemy should have an on-text rather than getting the
            # phrase directly, to allow for stuff doing things on miss etc.
            target = self._target()
            target.on_text(c)

    def _tile_coords_to_array_index(self, coords):
        """Work out the array slot for a given set of axial tile coords."""
        return Vector(coords.q - self._min_coords.q,
                      coords.r - self._min_coords.r)

    def _lookup_tile(self, coords):
        """Look up a tile from its (q, r) coordinates."""
        if not self._tile_coords_valid:
            return None
        index = self._tile_coords_to_array_index(coords)
        return self._tiles[index.y, index.x]

    def _screen_coords_to_tile(self, coords):
        """Work out which tile a given point in screen coordinates is in."""
        pixel_info = self._picking_texture.read(coords.x, coords.y)

        # The blue value will be 0 if no tile was hit
        if pixel_info[2] == 0:
            return None

        # The q and r coordinates are stored in the r and g values, respectively
        return self._lookup_tile(Vector(pixel_info[0], pixel_info[1]))

    def _screen_coords_to_tile_coords(self, coords):
        """Convert screen coordinates to tile coordinates.

        Returns a vector containing the coordinates on the q and r axes.

        This will return a value even if there is no tile currently at the
        coordinates (in contrast to _screen_coords_to_tile). This does not
        take into account the height of tiles - it unprojects the click to
        world-space with a Z-value of 0."""
        world_coords = self._cam.unproject(coords, 0)
        return Tile.world_to_tile_coords(world_coords)

    def _tile_coords_valid(self, tc):
        """Determine whether a given set of tile coordinates is within range."""
        return (tc.q >= self._min_coords.q and tc.q <= self._max_coords.q and
                tc.r >= self._min_coords.r and tc.r <= self._max_coords.r)

    def _tile_neighbours(self, tile):
        """Find the neighbouring tiles for a given tile.

        Takes a Tile and returns a list of Tiles.
        Does not consider whether a given tile is empty or not.
        """
        dirs = [(+1, 0), (+1, -1), (0, -1), (-1, 0), (-1, 1), (0, 1)]
        neighbours = []
        for d in dirs:
            neighbour_coords = Vector(tile.q + d[0], tile.r + d[1])
            neighbour = self._lookup_tile(neighbour_coords)
            if neighbour:
                neighbours.append(neighbour)
        return neighbours

    def _build_paths(self):
        """Calculate paths from each tile to the base."""
        # Clear any previous path info
        for _, tile in numpy.ndenumerate(self._tiles):
            if tile:
                tile.path_next = None

        # TODO: Start a 0,0 for now, but eventually will have to work out where
        # the base is and start there.
        start = self._lookup_tile(Vector(0, 0))
        if not start:
            return

        frontier = deque([start])
        visited = set([start])
        while len(frontier) > 0:
            tile = frontier.popleft()

            for nxt in [t for t in self._tile_neighbours(tile)
                        if t.empty and t not in visited]:
                frontier.append(nxt)
                visited.add(nxt)
                nxt.path_next = tile

    def _update_target(self, c):
        """Check whether we have a target, and find a new one if not."""
        if not self._target or not self._target():
            targets = [enemy for enemy in self._enemies
                       if enemy.phrase.start == c]
            if targets:
                self._target = weakref.ref(targets[0])
