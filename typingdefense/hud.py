import numpy
import OpenGL.GL as GL
import typingdefense.tower as tower
from .text import Text, Text2D
from .glutils import VertexArray, VertexBuffer


class Button(object):
    SIZE = 32

    def __init__(self, app, x, y):
        self._app = app
        self._vao = VertexArray()
        self._vbo = VertexBuffer()
        self.x = x
        self.y = y

        self._shader = app.resources.load_shader_program('ortho.vs',
                                                         'test.fs')
        self._screen_uniform = self._shader.uniform('screenDimensions')

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

    def draw(self):
        self._shader.use()
        GL.glUniform2f(self._screen_uniform,
                       self._app.window_width, self._app.window_height)

        with self._vao.bind():
            GL.glDrawArrays(GL.GL_LINE_LOOP, 0, 4)

        GL.glUseProgram(0)

    def hit(self, x, y):
        return (x <= self.x + Button.SIZE and
                x >= self.x - Button.SIZE and
                y <= self.y + Button.SIZE and
                y >= self.y - Button.SIZE)


class Hud(object):
    def __init__(self, app, level):
        font = app.resources.load_font("hudfont.fnt")
        self._level = level
        self._test_text = Text2D(app, font, "HUD", 400, 10, 32,
                                 Text.Align.center)

        # TODO: List of buttons, lambdas for behaviours?
        self._play_button = Button(app, 10, 20)
        self._slow_tower_button = Button(app, 70, 20)

    def draw(self):
        self._test_text.draw()
        self._play_button.draw()
        self._slow_tower_button.draw()

    def on_click(self, x, y):
        if self._play_button.hit(x, y):
            self._level.play()
            return True
        elif self._slow_tower_button.hit(x, y):
            self._level.tower_creator = tower.SlowTower
            return True
        return False
