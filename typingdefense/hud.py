"""Module for the in-game HUD."""
import numpy
import OpenGL.GL as GL
import typingdefense.tower as tower
from enum import Enum, unique
from .text import Text, Text2D
from .glutils import VertexArray, VertexBuffer, ShaderInstance


class Button(object):
    SIZE = 32

    def __init__(self, app, x, y):
        self._app = app
        self._vao = VertexArray()
        self._vbo = VertexBuffer()
        self.x = x
        self.y = y

        self._shader = ShaderInstance(
            app, 'ortho.vs', 'test.fs',
            [('screenDimensions', GL.GL_FLOAT_VEC2, [app.window_width,
                                                     app.window_height]),
             ('translate', GL.GL_FLOAT_VEC2, [0, 0])])

        data = [x - Button.SIZE / 2, y - Button.SIZE / 2,
                x - Button.SIZE / 2, y + Button.SIZE / 2,
                x + Button.SIZE / 2, y + Button.SIZE / 2,
                x + Button.SIZE / 2, y - Button.SIZE / 2]

        with self._vao.bind():
            self._vbo.bind()
            data_array = numpy.array(data, numpy.float32)
            GL.glBufferData(GL.GL_ARRAY_BUFFER,
                            data_array.nbytes, data_array,
                            GL.GL_STATIC_DRAW)
            GL.glEnableVertexAttribArray(0)
            GL.glVertexAttribPointer(0, 2, GL.GL_FLOAT, GL.GL_FALSE, 8, None)

    def draw(self, translate=None):
        if translate is not None:
            self._shader.set_uniform('translate', translate, download=False)
        else:
            self._shader.set_uniform('translate', [0, 0], download=False)

        with self._shader.use():
            with self._vao.bind():
                GL.glDrawArrays(GL.GL_LINE_LOOP, 0, 4)

    def hit(self, x, y):
        return (x <= self.x + Button.SIZE and
                x >= self.x - Button.SIZE and
                y <= self.y + Button.SIZE and
                y >= self.y - Button.SIZE)


class Hud(object):
    """The in-game HUD."""
    @unique
    class AnimationState(Enum):
        """Enumeration of HUD animation states."""
        none = 1
        defend_starting = 2
        defend_ending = 3

    _ANIMATION_TIME = 0.5

    def __init__(self, app, level):
        font = app.resources.load_font('hudfont.fnt')
        self._level = level
        self._animation_change_time = 0
        self._animation_state = Hud.AnimationState.none

        self._money = Text2D(app, font, str(level.money),
                             app.window_width / 2, app.window_height - 32, 32,
                             Text.Align.center)

        self._play_button = Button(app, 20, 20)
        self._slow_tower_button = Button(app, 70, 20)
        self._kill_tower_button = Button(app, 120, 20)
        self._money_tower_button = Button(app, 170, 20)

    def draw(self):
        self._money.text = str(self._level.money)
        self._money.draw()

        if (self._animation_state != Hud.AnimationState.none and
                self._level.timer.time - Hud._ANIMATION_TIME >
                self._animation_change_time):
            self._animation_state = Hud.AnimationState.none

        # Work out where the build buttons should be.
        translate = [0, 0]
        if self._animation_state == Hud.AnimationState.defend_ending:
            # The defend phase is ending, move the build buttons onto the screen.
            ratio = 1 - ((self._level.timer.time -
                          self._animation_change_time) / Hud._ANIMATION_TIME)
            translate[1] = -40 * ratio
        elif self._animation_state == Hud.AnimationState.defend_starting:
            # The defend phase is starting, move the build buttons off the
            # screen.
            ratio = ((self._level.timer.time - self._animation_change_time) /
                     Hud._ANIMATION_TIME)
            translate[1] = -40 * ratio

        from .level import Level
        if (self._animation_state != Hud.AnimationState.none or
                self._level.state == Level.State.build):
            self._play_button.draw(translate)
            self._slow_tower_button.draw(translate)
            self._kill_tower_button.draw(translate)
            self._money_tower_button.draw(translate)

    def on_click(self, x, y):
        if self._play_button.hit(x, y):
            self._level.play()
            return True
        elif self._slow_tower_button.hit(x, y):
            self._level.tower_creator = tower.SlowTower
            return True
        elif self._kill_tower_button.hit(x, y):
            self._level.tower_creator = tower.KillTower
        elif self._money_tower_button.hit(x, y):
            self._level.tower_creator = tower.MoneyTower
        return False

    def animate_defend_phase_end(self):
        self._animation_change_time = self._level.timer.time
        self._animation_state = Hud.AnimationState.defend_ending

    def animate_defend_phase_start(self):
        self._animation_change_time = self._level.timer.time
        self._animation_state = Hud.AnimationState.defend_starting
