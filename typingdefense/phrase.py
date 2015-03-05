"""Module for managing in-game phrases."""
from typingdefense.text import Text
from OpenGL import GL


class PhraseText(Text):
    """Class for displaying text for a phrase.

    This is text associated with a position in the (3D) game world, but
    projected so that it appears the same size regardless of depth."""
    def __init__(self, app, cam, font, text, x, y, height,
                 align=Text.Align.left):
        super().__init__(font, text, x, y, height, align)

        self._app = app
        self._cam = cam
        # TODO: Use ShaderInstance
        self._shader = app.resources.load_shader_program('phrase_text.vs',
                                                         'phrase_text.fs')
        self._transmatrix_uniform = self._shader.uniform('transMatrix')
        self._origin_uniform = self._shader.uniform('origin')
        self._screen_uniform = self._shader.uniform('screenDimensions')
        self._texunit_uniform = self._shader.uniform('texUnit')
        self._colour_uniform = self._shader.uniform('inColour')

    def draw(self, x, y, z, typedchars):
        """Draw the text."""
        self._shader.use()
        GL.glUniformMatrix4fv(self._transmatrix_uniform, 1, GL.GL_TRUE,
                              self._cam.trans_matrix_as_array())
        GL.glUniform3f(self._origin_uniform, x, y, z)
        GL.glUniform2f(self._screen_uniform,
                       self._app.window_width, self._app.window_height)
        GL.glUniform1i(self._texunit_uniform, 0)

        GL.glDisable(GL.GL_DEPTH_TEST)
        with self._vao.bind():
            GL.glUniform3f(self._colour_uniform, 1, 0, 0)
            for i in range(len(self._text)):
                if i == typedchars:
                    GL.glUniform3f(self._colour_uniform, 1, 1, 1)
                GL.glDrawArrays(GL.GL_TRIANGLE_STRIP, i * 4, 4)
        GL.glEnable(GL.GL_DEPTH_TEST)
        GL.glUseProgram(0)


class Phrase(object):
    """Class representing an in-game phrase."""

    def __init__(self, app, cam, phrase):
        font = app.resources.load_font("menufont.fnt")
        self._text = PhraseText(app, cam, font, phrase, 0, 0, 48,
                                Text.Align.center)
        self._typed_chars = 0
        self._hit = False

    @property
    def complete(self):
        """Whether the phrase has been completed."""
        return len(self._text.text) == self._typed_chars

    @property
    def hit(self):
        """Whether the last character typed was correct."""
        return self._hit

    @property
    def start(self):
        """Returns the first character of the phrase."""
        return self._text.text[0]

    def on_type(self, c):
        """Update the phrase on typing text targetted at it."""
        if self._typed_chars < len(self._text.text):
            if c == self._text.text[self._typed_chars]:
                self._typed_chars += 1
                self._hit = True
            else:
                self._hit = False

    def draw(self, origin):
        """Draw the phrase."""
        self._text.draw(origin.x, origin.y, origin.z, self._typed_chars)
