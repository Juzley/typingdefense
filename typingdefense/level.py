"""Module containing all classes required to represent and handle a level."""
import math
import numpy
import weakref
import json
import copy
import ctypes
from collections import deque
from enum import Enum, unique
from OpenGL import GL
import typingdefense.glutils as glutils
import typingdefense.camera as camera
import typingdefense.vector as vector
import typingdefense.enemy as enemy
import typingdefense.util as util
import typingdefense.hud as hud
import typingdefense.phrasebook as phrasebook


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

    return vector.Vector(rx, ry, rz)


def _hex_round(fh):
    """Round fractional axial-format hex coordinates."""
    return _cube_to_hex(_cube_round(_hex_to_cube(fh)))


def _hex_to_cube(h):
    """Convert axial-format hex coordinates to cube-format."""
    return vector.Vector(h.q, -h.q - h.r, h.r)


def _cube_to_hex(c):
    """Convert cube-format hex coordinates to hex."""
    return vector.Vector(c.x, c.z)


class Tile(object):
    """Class representing a single tile in a level."""
    SIZE = 1
    DEPTH = 2
    HEIGHT = SIZE * 2
    WIDTH = SIZE * (math.sqrt(3)/2) * HEIGHT
    VERT_SPACING = HEIGHT * 0.75
    HORIZ_SPACING = WIDTH

    def __init__(self, app, cam, coords, height, colour):
        """Construct a (hexagonal) tile.

        coords is a vector containing the horizontal coordinates of the tile,
        using axial coordinates.
        height is the number of stacks in the tile.
        """
        self.coords = coords
        self.height = height
        self.colour = colour
        self.path_next = None
        self.tower = None

        self._shader = glutils.ShaderInstance(
            app, 'level.vs', 'level.fs',
            [('transMatrix', GL.GL_FLOAT_MAT4, cam.trans_matrix_as_array()),
             ('colourIn', GL.GL_FLOAT_VEC4, None)])
        self._hex = glutils.Hex(vector.Vector(self.x, self.y, 0),
                                Tile.SIZE, Tile.DEPTH, height)

        self.outline_colour = colour
        self.face_colour = copy.copy(self.outline_colour)
        self.face_colour.s = self.face_colour.s / 2

        # Dictionary of waves, keyed by the level phase in which they appear.
        self.waves = {}

        # Whether the tile is a 'slow movement' tile.
        self.slow = False

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

    @property
    def top(self):
        """Calculate the world Z coord of the top of the tile."""
        return self.height * Tile.HEIGHT

    @staticmethod
    def world_to_tile_coords(world_coords):
        """Convert world (x, y) coordinates to tile (q, r) coordinates.

        Note that this is a 2D conversion only."""
        q = (world_coords.x * math.sqrt(3) / 3 - world_coords.y / 3) / Tile.SIZE
        r = (world_coords.y * 2 / 3) / Tile.SIZE
        return _hex_round(vector.Vector(q, r))

    @property
    def empty(self):
        """Indicate whether the tile has a tower on it."""
        return self.tower is None

    def draw(self, outline=True, faces=True,
             outline_colour=None, face_colour=None):
        """Draw the tile."""
        with self._shader.use(download_uniforms=False):
            self._shader.set_uniform('transMatrix')
            if faces:
                if face_colour is None:
                    self._shader.set_uniform('colourIn', self.face_colour)
                else:
                    self._shader.set_uniform('colourIn', face_colour)
                self._hex.draw_faces()

            if outline:
                if outline_colour is None:
                    self._shader.set_uniform('colourIn', self.outline_colour)
                else:
                    self._shader.set_uniform('colourIn', outline)
                with glutils.linewidth(2):
                    self._hex.draw_outline()

    def picking_draw(self, picking_shader):
        """Draw to the picking framebuffer.

        This allows us to determine which tile was hit by mouse events.
        """
        picking_shader.set_uniform('colourIn',
                                   [self.coords.q, self.coords.r, 0, 0])
        self._hex.draw_faces()


class Base(object):
    """Class representing the player's base."""
    START_HEALTH = 100

    def __init__(self, app, cam, tile, origin, z):
        self.health = Base.START_HEALTH
        self.tile = tile

        self._shader = glutils.ShaderInstance(
            app, 'level.vs', 'level.fs',
            [('transMatrix', GL.GL_FLOAT_MAT4, cam.trans_matrix_as_array())])
        self._hex = glutils.Hex(vector.Vector(tile.x, tile.y, 0),
                                Tile.SIZE * 0.8, Tile.DEPTH, 2)

    def draw(self):
        """Draw the base."""
        with self._shader.use():
            self._hex.draw()

    def damage(self, dmg):
        self.health -= dmg
        # TODO: Death


class Level(object):
    """Class representing a game level."""

    @unique
    class State(Enum):
        """Enumeration of different level states."""
        defend = 1
        build = 2

    def __init__(self, app, game):
        self._app = app
        self.cam = camera.Camera(
            origin=[0, -30, 60], target=[0, 0, 0], up=[0, 1, 0], fov=50,
            screen_width=app.window_width, screen_height=app.window_height,
            near=0.1, far=1000)
        self.phrases = phrasebook.PhraseBook('resources/phrases/all.phr')

        # Level state
        self.timer = util.Timer()
        self.money = 0
        self.state = Level.State.build
        self._target = None
        self._phase = 0
        self._towers = []
        self.enemies = []
        self.waves = []
        self.tower_creator = None

        # Map/graphics etc.
        self._min_coords = None
        self._max_coords = None
        self.tiles = None
        self.base = None
        self.load()

        self._vao = None
        self._vbo = None
        self._shader = glutils.ShaderInstance(
            self._app, 'level2.vs', 'level2.fs',
            [('transMatrix', GL.GL_FLOAT_MAT4,
              self.cam.trans_matrix_as_array()),
             ('colourIn', GL.GL_FLOAT_VEC4, [1, 1, 1, 1])])
        self._build_vertex_arrays()

        self._picking_texture = glutils.PickingTexture(app.window_width,
                                                       app.window_height)
        self._picking_shader = glutils.ShaderInstance(
            app, 'level.vs', 'picking.fs',
            [['transMatrix', GL.GL_FLOAT_MAT4,
              self.cam.trans_matrix_as_array()],
             ['colourIn', GL.GL_FLOAT_VEC4, [0, 0, 0, 0]]])
        self.picking_draw()

        self._hud = hud.Hud(app, self)

    def load(self):
        """Load the level."""
        self._min_coords = vector.Vector(-100, -100)
        self._max_coords = vector.Vector(100, 100)

        width = self._max_coords.x - self._min_coords.x + 1
        height = self._max_coords.y - self._min_coords.y + 1
        self.tiles = numpy.empty([height, width], dtype=object)
        try:
            with open('resources/levels/test_level.tdl', 'r') as f:
                lvl_info = json.load(f)
                # Load tiles
                for tile_info in lvl_info['tiles']:
                    coords = vector.Vector(tile_info['q'], tile_info['r'])
                    colour = util.Colour(tile_info['colour']['r'],
                                         tile_info['colour']['g'],
                                         tile_info['colour']['b'],
                                         tile_info['colour']['a'])
                    idx = self.tile_coords_to_array_index(coords)
                    self.tiles[idx.y, idx.x] = Tile(self._app,
                                                    self.cam,
                                                    coords,
                                                    tile_info['height'],
                                                    colour)

                # Load Waves
                phase_idx = 0
                if 'waves' in lvl_info:
                    for phase_info in lvl_info['waves']:
                        waves = []
                        for wave_info in phase_info:
                            coords = vector.Vector(wave_info['q'],
                                                   wave_info['r'])
                            tile = self.lookup_tile(coords)
                            wave = enemy.Wave(
                                self._app, self, tile,
                                enemy_count=wave_info['enemy_count'],
                                start_time=wave_info['start_time'],
                                spawn_gap=wave_info['spawn_gap'],
                                enemy_type=wave_info['enemy_type'])
                            tile.waves[phase_idx] = wave
                            waves.append(wave)
                        self.waves.append(waves)
                        phase_idx += 1

        except FileNotFoundError:
            pass

        tile = self.lookup_tile(vector.Vector(0, 0))
        self.base = Base(self._app, self.cam, tile, vector.Vector(0, 0),
                         Tile.HEIGHT)

        self.money = 500

    def save(self):
        """Save the edited level to file."""
        level = {}
        level['name'] = 'Test Level'

        tiles = []
        for _, tile in numpy.ndenumerate(self.tiles):
            if tile:
                colour = {'r': tile.colour.r,
                          'g': tile.colour.g,
                          'b': tile.colour.b,
                          'a': tile.colour.a}
                tiles.append({'q': tile.q, 'r': tile.r, 'height': tile.height,
                              'colour': colour})
        level['tiles'] = tiles

        phases = []
        for phase in self.waves:
            waves = []
            for wave in phase:
                waves.append({'q': wave.tile.q, 'r': wave.tile.r,
                              'enemy_type': wave.enemy_type.__name__,
                              'enemy_count': wave.enemy_count,
                              'start_time': wave.start_time,
                              'spawn_gap': wave.spawn_gap})
            phases.append(waves)

        level['waves'] = phases

        with open('resources/levels/test_level.tdl', 'w') as f:
            json.dump(level, f)

    def picking_draw(self):
        """Draw the tiles to the picking buffer."""
        with self._picking_texture.enable():
            with self._picking_shader.use(download_uniforms=False):
                GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
                self._picking_shader.set_uniform('transMatrix')
                for tile_list in self.tiles:
                    for tile in tile_list:
                        if tile:
                            tile.picking_draw(self._picking_shader)

    def draw(self):
        """Draw the level."""
        self._draw_vertex_arrays()
        self.base.draw()

        for tower in self._towers:
            tower.draw()
        for e in self.enemies:
            e.draw()

        self._hud.draw()

    def play(self):
        """Move from build into play state."""
        if self.state == Level.State.build:
            self._build_paths()
            self._hud.animate_defend_phase_start()
            self.state = Level.State.defend
            self._phase += 1

    def update(self):
        """Advance the game state."""
        self.timer.update()

        if self.state == Level.State.defend:
            # Update enemies
            for e in self.enemies:
                e.update(self.timer)
            for e in [e for e in self.enemies if e.unlink]:
                self.enemies.remove(e)

            # Update towers
            for tower in self._towers:
                tower.update()

            # Spawn new enemies
            active_waves = False
            for wave in self.waves[self._phase - 1]:
                wave.update(self.timer)

                if not wave.finished:
                    active_waves = True

            # Check if the current phase is finished.
            if not active_waves and len(self.enemies) == 0:
                self._hud.animate_defend_phase_end()
                self.state = Level.State.build
                # TODO: Check if we've finished the last phase.

    def on_click(self, x, y, button):
        """Handle a mouse click."""

        if self.state == Level.State.build:
            hit_hud = self._hud.on_click(x, y)

            if not hit_hud:
                tile = self.screen_coords_to_tile(vector.Vector(x, y))
                if tile and tile.empty:
                    # TODO: Check if the tower ends up leaving no route to the
                    # base
                    if (self.tower_creator is not None and
                            self.money >= self.tower_creator.COST):
                        tower = self.tower_creator(self._app, self, tile)
                        self._towers.append(tower)
                        tile.tower = tower
                        self.money -= tower.COST

    def on_keydown(self, key):
        """Handle keydown events."""
        pass

    def on_text(self, c):
        """Handle text input."""
        self._update_target(c)
        if self._target and self._target():
            target = self._target()
            target.on_text(c)

    def add_enemy(self, e):
        """Add an enemy to the level."""
        self.enemies.append(e)

    def tile_coords_to_array_index(self, coords):
        """Work out the array slot for a given set of axial tile coords."""
        return vector.Vector(coords.q - self._min_coords.q,
                             coords.r - self._min_coords.r)

    def iter_tiles(self):
        """Generator function for the level's tiles."""
        for tile_list in self.tiles:
            for tile in tile_list:
                if tile is not None:
                    yield tile

    def lookup_tile(self, coords):
        """Look up a tile from its (q, r) coordinates."""
        if not self.tile_coords_valid:
            return None
        index = self.tile_coords_to_array_index(coords)
        return self.tiles[index.y, index.x]

    def screen_coords_to_tile(self, coords):
        """Work out which tile a given point in screen coordinates is in."""
        pixel_info = self._picking_texture.read(coords.x, coords.y)

        # The blue value will be 0 if no tile was hit
        if pixel_info[2] == 0:
            return None

        # The q and r coordinates are stored in the r and g values, respectively
        return self.lookup_tile(vector.Vector(pixel_info[0], pixel_info[1]))

    def screen_coords_to_tile_coords(self, coords):
        """Convert screen coordinates to tile coordinates.

        Returns a vector containing the coordinates on the q and r axes.

        This will return a value even if there is no tile currently at the
        coordinates (in contrast to screen_coords_to_tile). This does not
        take into account the height of tiles - it unprojects the click to
        world-space with a Z-value of 0."""
        world_coords = self.cam.unproject(coords, 0)
        return Tile.world_to_tile_coords(world_coords)

    def tile_coords_valid(self, tc):
        """Determine whether a given set of tile coordinates is within range."""
        return (tc.q >= self._min_coords.q and tc.q <= self._max_coords.q and
                tc.r >= self._min_coords.r and tc.r <= self._max_coords.r)

    def tile_neighbours(self, tile):
        """Find the neighbouring tiles for a given tile.

        Takes a Tile and returns a list of Tiles.
        Does not consider whether a given tile is empty or not.
        """
        dirs = [(+1, 0), (+1, -1), (0, -1), (-1, 0), (-1, 1), (0, 1)]
        neighbours = []
        for d in dirs:
            neighbour_coords = vector.Vector(tile.q + d[0], tile.r + d[1])
            neighbour = self.lookup_tile(neighbour_coords)
            if neighbour:
                neighbours.append(neighbour)
        return neighbours

    def _build_paths(self):
        """Calculate paths from each tile to the base."""
        # Clear any previous path info
        for _, tile in numpy.ndenumerate(self.tiles):
            if tile:
                tile.path_next = None

        # TODO: Start a 0,0 for now, but eventually will have to work out where
        # the base is and start there.
        start = self.lookup_tile(vector.Vector(0, 0))
        if not start:
            return

        # TODO: consider height

        frontier = deque([start])
        visited = set([start])
        while len(frontier) > 0:
            tile = frontier.popleft()

            for nxt in [t for t in self.tile_neighbours(tile)
                        if t.empty and t not in visited]:
                frontier.append(nxt)
                visited.add(nxt)
                nxt.path_next = tile

    def _build_vertex_arrays(self):
        # TODO: Could make data smaller with indirect buffers
        all_verts = []
        for tile in self.iter_tiles():
            for s in range(tile.height):
                face_top_verts, face_vert_verts = ([], [])
                line_top_verts, line_vert_verts = ([], [])
                for i in range(6):
                    angle = 2 * math.pi / 6
                    z = 0 + Tile.DEPTH * s
                    px = tile.x + Tile.SIZE * math.sin(angle * (5 - i))
                    py = tile.y + Tile.SIZE * math.cos(angle * (5 - i))
                    face_top_verts.extend([px, py, z + Tile.DEPTH,
                                           tile.face_colour.r,
                                           tile.face_colour.g,
                                           tile.face_colour.b,
                                           tile.face_colour.a])
                    line_top_verts.extend([px, py, z + Tile.DEPTH,
                                           tile.outline_colour.r,
                                           tile.outline_colour.g,
                                           tile.outline_colour.b,
                                           tile.outline_colour.a])

                    px = tile.x + Tile.SIZE * math.sin(angle * i)
                    py = tile.y + Tile.SIZE * math.cos(angle * i)
                    face_vert_verts.extend([px, py, z,
                                            tile.face_colour.r,
                                            tile.face_colour.g,
                                            tile.face_colour.b,
                                            tile.face_colour.a,
                                            px, py, z + Tile.DEPTH,
                                            tile.face_colour.r,
                                            tile.face_colour.g,
                                            tile.face_colour.b,
                                            tile.face_colour.a])
                    line_vert_verts.extend([px, py, z,
                                            tile.face_colour.r,
                                            tile.face_colour.g,
                                            tile.face_colour.b,
                                            tile.face_colour.a,
                                            px, py, z + Tile.DEPTH,
                                            tile.face_colour.r,
                                            tile.face_colour.g,
                                            tile.face_colour.b,
                                            tile.face_colour.a])
                all_verts.extend(face_top_verts + face_vert_verts +
                                 line_top_verts + line_vert_verts)

        verts = numpy.array(all_verts, numpy.float32)
        self._vao = glutils.VertexArray()
        self._vbo = glutils.VertexBuffer()
        with self._vao.bind():
            self._vbo.bind()
            GL.glBufferData(GL.GL_ARRAY_BUFFER, verts.nbytes, verts,
                            GL.GL_STATIC_DRAW)
            GL.glEnableVertexAttribArray(0)
            GL.glVertexAttribPointer(0, 3, GL.GL_FLOAT, GL.GL_FALSE, 7 * 4,
                                     None)
            GL.glEnableVertexAttribArray(1)
            GL.glVertexAttribPointer(1, 4, GL.GL_FLOAT, GL.GL_FALSE, 7 * 4,
                                     ctypes.c_void_p(12))

    def _draw_vertex_arrays(self):
        with self._vao.bind(), self._shader.use():
            tile_count = len([t for t in self.iter_tiles()])
            for i in range(tile_count):
                GL.glDrawArrays(GL.GL_TRIANGLE_FAN, i * 36, 6)
                GL.glDrawArrays(GL.GL_TRIANGLE_STRIP, 6 + i * 36, 12)
                with glutils.linewidth(2):
                    GL.glDrawArrays(GL.GL_LINE_LOOP, 18 + i * 36, 6)
                    GL.glDrawArrays(GL.GL_LINES, 24 + i * 36, 12)

    def _update_target(self, c):
        """Check whether we have a target, and find a new one if not."""
        if not self._target or not self._target():
            targets = [enemy for enemy in self.enemies
                       if enemy.phrase.start == c]
            if targets:
                self._target = weakref.ref(targets[0])
