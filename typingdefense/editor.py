"""Level editor module."""
import sdl2
import numpy
from OpenGL import GL
from enum import Enum, unique
from .glutils import VertexArray, VertexBuffer, ShaderInstance
from .util import Colour
from .enemy import Wave
from .vector import Vector
from .level import Tile


class ColourButton(object):
    SIZE = 32

    def __init__(self, app, coords):
        self._shader = ShaderInstance(
            app, 'ortho.vs', 'level.fs',
            [('screenDimensions', GL.GL_FLOAT_VEC2,
              (app.window_width, app.window_height)),
             ('colourIn', GL.GL_FLOAT_VEC4, [1, 1, 1, 1])])

        self._vao = VertexArray()
        self._vbo = VertexBuffer()
        self.coords = coords
        data = [coords.x + ColourButton.SIZE / 2,
                coords.y - ColourButton.SIZE / 2,
                coords.x + ColourButton.SIZE / 2,
                coords.y + ColourButton.SIZE / 2,
                coords.x - ColourButton.SIZE / 2,
                coords.y + ColourButton.SIZE / 2,
                coords.x - ColourButton.SIZE / 2,
                coords.y - ColourButton.SIZE / 2]
        with self._vao.bind():
            self._vbo.bind()
            data_array = numpy.array(data, numpy.float32)
            GL.glBufferData(GL.GL_ARRAY_BUFFER,
                            data_array.nbytes, data_array,
                            GL.GL_STATIC_DRAW)
            GL.glEnableVertexAttribArray(0)
            GL.glVertexAttribPointer(0, 2, GL.GL_FLOAT, GL.GL_FALSE, 8, None)

    def draw(self, colour):
        with self._shader.use():
            with self._vao.bind():
                self._shader.set_uniform('colourIn', Colour.from_white())
                GL.glDrawArrays(GL.GL_LINE_LOOP, 0, 4)
                self._shader.set_uniform('colourIn', colour)
                GL.glDrawArrays(GL.GL_TRIANGLE_FAN, 0, 4)


class EditorHud(object):
    def __init__(self, app, editor):
        self._editor = editor
        self._colourbutton = ColourButton(app, Vector(10, 10))

    def draw(self):
        self._colourbutton.draw(self._editor.colour)


class Editor(object):
    @unique
    class State(Enum):
        """Enumeration of different editor modes."""
        tile = 1
        wave = 2
        base = 3

    def __init__(self, app, level):
        self._state = Editor.State.tile
        self._app = app
        self._level = level

        self._colours = [Colour(243/255, 112/255, 82/255),
                         Colour(251/255, 177/255, 96/255),
                         Colour(255/255, 218/255, 119/255),
                         Colour(180/255, 214/255, 111/255),
                         Colour(29/255, 185/255, 199/255),
                         Colour(144/255, 167/255, 213/255),
                         Colour(170/255, 116/255, 177/255)]
        self._colour_index = 0
        self._hud = EditorHud(app, self)

    def draw(self):
        self._level.picking_draw()

        for _, tile in numpy.ndenumerate(self._level.tiles):
            if tile:
                # TODO: Hardcoded phase here
                draw_faces = (0 in tile.waves or
                              self._state != Editor.State.wave)
                tile.draw(faces=draw_faces)

        self._level.base.draw()
        self._hud.draw()

    def update(self):
        pass

    def on_keydown(self, key):
        """Handle keydown events."""
        if key == sdl2.SDLK_s:
            self._level.save()
        elif key == sdl2.SDLK_t:
            self._state = Editor.State.tile
        elif key == sdl2.SDLK_w:
            self._state = Editor.State.wave
        elif key == sdl2.SDLK_b:
            self._state = Editor.State.base
        elif key == sdl2.SDLK_c:
            self.next_colour()

    def on_text(self, c):
        """Handle text input."""
        pass

    def on_click(self, x, y, button):
        """Handle a mouse click."""
        if button != sdl2.SDL_BUTTON_LEFT and button != sdl2.SDL_BUTTON_RIGHT:
            return

        add = (button == sdl2.SDL_BUTTON_LEFT)
        tile = self._level.screen_coords_to_tile(Vector(x, y))

        if self._state == Editor.State.tile:
            if tile:
                tile_coords = tile.coords
                height = tile.height + (1 if add else -1)
                colour = tile.colour
            else:
                tile_coords = self._level.screen_coords_to_tile_coords(
                        Vector(x, y))
                height = 1 if add else 0
                colour = self.colour

            if self._level.tile_coords_valid(tile_coords):
                index = self._level.tile_coords_to_array_index(tile_coords)
                if height > 0:
                    self._level.tiles[index.y, index.x] = Tile(self._app,
                                                               self._level.cam,
                                                               tile_coords,
                                                               height,
                                                               colour)
                else:
                    self._level.tiles[index.y, index.x] = None

        elif self._state == Editor.State.wave:
            # TODO: Hardcoded phase
            phase = 0
            if add and tile and phase not in tile.waves:
                wave = Wave(self._app, self._level, tile)

                # Extend the wave list if it is not long enough.
                self._level.waves += [[]] * (phase + 1 - len(self._level.waves))
                self._level.waves[phase].append(wave)
                tile.waves[phase] = wave

            if not add and tile and phase in tile.waves:
                wave = tile.waves[phase]

                self._level.waves[phase].remove(wave)
                del(tile.waves[phase])
        elif self._state == Editor.State.base:
            if tile:
                # TODO: Move the base
                pass

    @property
    def colour(self):
        return self._colours[self._colour_index]

    def next_colour(self):
        if self._colour_index + 1 == len(self._colours):
            self._colour_index = 0
        else:
            self._colour_index += 1
