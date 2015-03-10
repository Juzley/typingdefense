"""Level editor module."""
import sdl2
import numpy
import itertools
from OpenGL import GL
from enum import Enum, unique
from .glutils import VertexArray, VertexBuffer, ShaderInstance
from .util import Colour
from .enemy import Wave, enemy_types
from .vector import Vector
from .level import Tile
from .text import Text2D


class _ColourButton(object):
    """A button to display the currently selected tile colour."""
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
        data = [coords.x + _ColourButton.SIZE / 2,
                coords.y - _ColourButton.SIZE / 2,
                coords.x + _ColourButton.SIZE / 2,
                coords.y + _ColourButton.SIZE / 2,
                coords.x - _ColourButton.SIZE / 2,
                coords.y + _ColourButton.SIZE / 2,
                coords.x - _ColourButton.SIZE / 2,
                coords.y - _ColourButton.SIZE / 2]
        with self._vao.bind():
            self._vbo.bind()
            data_array = numpy.array(data, numpy.float32)
            GL.glBufferData(GL.GL_ARRAY_BUFFER,
                            data_array.nbytes, data_array,
                            GL.GL_STATIC_DRAW)
            GL.glEnableVertexAttribArray(0)
            GL.glVertexAttribPointer(0, 2, GL.GL_FLOAT, GL.GL_FALSE, 8, None)

    def draw(self, colour):
        """Draw the button."""
        with self._shader.use():
            with self._vao.bind():
                self._shader.set_uniform('colourIn', Colour.from_white())
                GL.glDrawArrays(GL.GL_LINE_LOOP, 0, 4)
                self._shader.set_uniform('colourIn', colour)
                GL.glDrawArrays(GL.GL_TRIANGLE_FAN, 0, 4)


class _EditorHud(object):
    """The HUD of the editor."""
    def __init__(self, app, editor):
        self._editor = editor
        self._colourbutton = _ColourButton(app, Vector(10, 10))

        font = app.resources.load_font('menufont.fnt')
        self._enemy_type_text = Text2D(app, font, '', 0, 0, 24)
        self._enemy_count_text = Text2D(app, font, '', 0, 24, 24)
        self._start_time_text = Text2D(app, font, '', 0, 48, 24)
        self._spawn_gap_text = Text2D(app, font, '', 0, 72, 24)
        self._phase_text = Text2D(app, font, '', 0, app.window_height - 24, 24)

    def draw(self):
        """Draw the HUD."""
        if self._editor.state == Editor.State.tile:
            self._colourbutton.draw(self._editor.colour)

        if self._editor.state == Editor.State.wave:
            phase_str = 'Phase: {}'.format(self._editor.phase)
            if self._editor.wave_edit_mode == Editor.WaveEditMode.phase:
                phase_str += ' +/-'
            self._phase_text.draw(phase_str)

        if self._editor.selected_wave is not None:
            enemy_type_str = self._editor.selected_wave.enemy_type.__name__
            if self._editor.wave_edit_mode == Editor.WaveEditMode.enemy_type:
                enemy_type_str += ' +/-'

            enemy_count_str = 'Count: {}'.format(
                self._editor.selected_wave.enemy_count)
            if self._editor.wave_edit_mode == Editor.WaveEditMode.enemy_count:
                enemy_count_str += ' +/-'

            start_time_str = 'Start: {}'.format(
                self._editor.selected_wave.start_time)
            if self._editor.wave_edit_mode == Editor.WaveEditMode.start_time:
                start_time_str += ' +/-'

            spawn_gap_str = 'Spawn gap: {}'.format(
                self._editor.selected_wave.spawn_gap)
            if self._editor.wave_edit_mode == Editor.WaveEditMode.spawn_gap:
                spawn_gap_str += ' +/-'

            self._enemy_type_text.draw(enemy_type_str)
            self._enemy_count_text.draw(enemy_count_str)
            self._start_time_text.draw(start_time_str)
            self._spawn_gap_text.draw(spawn_gap_str)


class Editor(object):
    """The level editor."""
    @unique
    class State(Enum):
        """Enumeration of different editor modes."""
        tile = 1
        wave = 2
        base = 3

    @unique
    class WaveEditMode(Enum):
        """Enumeration of different wave editing modes."""
        enemy_type = 1
        enemy_count = 2
        start_time = 3
        spawn_gap = 4
        phase = 5

    def __init__(self, app, level):
        self.state = Editor.State.tile
        self.wave_edit_mode = Editor.WaveEditMode.enemy_count
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
        self._hud = _EditorHud(app, self)
        self.selected_wave = None
        self.enemy_type = enemy_types[0]
        self.phase = 0

    def draw(self):
        """Draw the level editor screen."""
        self._level.picking_draw()

        for _, tile in numpy.ndenumerate(self._level.tiles):
            if tile:
                draw_faces = (self.phase in tile.waves or
                              self.state != Editor.State.wave)
                if (self.phase in tile.waves and
                        self.selected_wave is tile.waves[self.phase]):
                    tile.draw(faces=draw_faces, face_colour=Colour.from_red())
                else:
                    tile.draw(faces=draw_faces)

        self._level.base.draw()
        self._hud.draw()

    def update(self):
        """Update the editor screen."""
        pass

    def on_keydown(self, key):
        """Handle keydown events."""
        if key == sdl2.SDLK_s:
            self._level.save()
        elif key == sdl2.SDLK_t:
            self.selected_wave = None
            self.state = Editor.State.tile
        elif key == sdl2.SDLK_w:
            self.state = Editor.State.wave
        elif key == sdl2.SDLK_b:
            self.selected_wave = None
            self.state = Editor.State.base
        elif key == sdl2.SDLK_c:
            self.next_colour()
        elif key == sdl2.SDLK_EQUALS:
            self._next_enemy()
            self._inc_enemy_count()
            self._inc_start_time()
            self._inc_spawn_gap()
            self._inc_phase()
        elif key == sdl2.SDLK_MINUS:
            self._prev_enemy()
            self._dec_enemy_count()
            self._dec_start_time()
            self._dec_spawn_gap()
            self._dec_phase()
        elif key == sdl2.SDLK_1:
            self.wave_edit_mode = Editor.WaveEditMode.enemy_type
        elif key == sdl2.SDLK_2:
            self.wave_edit_mode = Editor.WaveEditMode.enemy_count
        elif key == sdl2.SDLK_3:
            self.wave_edit_mode = Editor.WaveEditMode.start_time
        elif key == sdl2.SDLK_4:
            self.wave_edit_mode = Editor.WaveEditMode.spawn_gap
        elif key == sdl2.SDLK_5:
            self.wave_edit_mode = Editor.WaveEditMode.phase

    def on_text(self, c):
        """Handle text input."""
        pass

    def _handle_tile_state_click(self, x, y, button):
        """Handle a click in tile-editing state."""
        add = (button == sdl2.SDL_BUTTON_LEFT)
        tile = self._level.screen_coords_to_tile(Vector(x, y))

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

    def _handle_wave_state_click(self, x, y, button):
        """Handle a click in wave-editing state."""
        add = (button == sdl2.SDL_BUTTON_LEFT)
        tile = self._level.screen_coords_to_tile(Vector(x, y))

        if add and tile:
            if self.phase not in tile.waves:
                wave = Wave(self._app, self._level, tile,
                            enemy_type=self.enemy_type)

                # Extend the wave list if it is not long enough.
                self._level.waves += [[]] * (self.phase + 1 -
                                             len(self._level.waves))
                self._level.waves[self.phase].append(wave)
                tile.waves[self.phase] = wave

                self.selected_wave = wave
            else:
                self.selected_wave = tile.waves[self.phase]

        if not add and tile and self.phase in tile.waves:
            wave = tile.waves[self.phase]

            self._level.waves[self.phase].remove(wave)
            del(tile.waves[self.phase])

    def _handle_base_state_click(self, x, y, button):
        """Handle a click in base-editing state."""
        # TODO
        pass

    def on_click(self, x, y, button):
        """Handle a mouse click."""
        if button != sdl2.SDL_BUTTON_LEFT and button != sdl2.SDL_BUTTON_RIGHT:
            return

        if self.state == Editor.State.tile:
            self._handle_tile_state_click(x, y, button)
        elif self.state == Editor.State.wave:
            self._handle_wave_state_click(x, y, button)
        elif self.state == Editor.State.base:
            self._handle_base_state_click(x, y, button)

    @property
    def colour(self):
        """Return the currently selected tile colour."""
        return self._colours[self._colour_index]

    def next_colour(self):
        """Cycle to the next tile colour."""
        if self._colour_index + 1 == len(self._colours):
            self._colour_index = 0
        else:
            self._colour_index += 1

    def _next_enemy(self):
        """Cycle to the next enemy type."""
        if (self.state == Editor.State.wave and
                self.wave_edit_mode == Editor.WaveEditMode.enemy_type and
                self.selected_wave is not None):
            idx = enemy_types.index(self.selected_wave.enemy_type)
            self.selected_wave.enemy_type = next(
                itertools.cycle(enemy_types[idx + 1:] + enemy_types[:idx + 1]))

    def _prev_enemy(self):
        """Cycle to the previous enemy type."""
        if (self.state == Editor.State.wave and
                self.wave_edit_mode == Editor.WaveEditMode.enemy_type and
                self.selected_wave is not None):
            types = list(reversed(enemy_types))
            idx = types.index(self.selected_wave.enemy_type)
            self.selected_wave.enemy_type = next(
                itertools.cycle(types[idx + 1:] + types[:idx + 1]))

    def _inc_enemy_count(self):
        """Increment the selected wave's enemy count."""
        if (self.state == Editor.State.wave and
                self.wave_edit_mode == Editor.WaveEditMode.enemy_count and
                self.selected_wave is not None):
            self.selected_wave.enemy_count += 1

    def _dec_enemy_count(self):
        """Decrement the selected wave's enemy count."""
        if (self.state == Editor.State.wave and
                self.wave_edit_mode == Editor.WaveEditMode.enemy_count and
                self.selected_wave is not None and
                self.selected_wave.enemy_count > 1):
            self.selected_wave.enemy_count -= 1

    def _inc_start_time(self):
        """Increment the selected wave's start time."""
        if (self.state == Editor.State.wave and
                self.wave_edit_mode == Editor.WaveEditMode.start_time and
                self.selected_wave is not None):
            self.selected_wave.start_time += 1

    def _dec_start_time(self):
        """Decrement the selected wave's start time."""
        if (self.state == Editor.State.wave and
                self.wave_edit_mode == Editor.WaveEditMode.start_time and
                self.selected_wave is not None and
                self.selected_wave.start_time > 0):
            self.selected_wave.start_time -= 1

    def _inc_spawn_gap(self):
        """Increment the selected wave's spawn gap."""
        if (self.state == Editor.State.wave and
                self.wave_edit_mode == Editor.WaveEditMode.spawn_gap and
                self.selected_wave is not None):
            self.selected_wave.spawn_gap += 1

    def _dec_spawn_gap(self):
        """Decrement the selected wave's spawn gap."""
        if (self.state == Editor.State.wave and
                self.wave_edit_mode == Editor.WaveEditMode.spawn_gap and
                self.selected_wave is not None and
                self.selected_wave.spawn_gap > 1):
            self.selected_wave.spawn_gap -= 1

    def _inc_phase(self):
        """Increment the wave phase."""
        if (self.state == Editor.State.wave and
                self.wave_edit_mode == Editor.WaveEditMode.phase and
                len(self._level.waves) > self.phase and
                len(self._level.waves[self.phase]) > 0):
            self.selected_wave = None
            self.phase += 1

    def _dec_phase(self):
        """Decrement the wave phase."""
        if (self.state == Editor.State.wave and
                self.wave_edit_mode == Editor.WaveEditMode.phase and
                self.phase > 0):
            self.selected_wave = None
            self.phase -= 1
