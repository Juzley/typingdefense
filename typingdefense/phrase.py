"""Module for managing in-game phrases."""
from OpenGL import GL
from typingdefense.text import Text
import typingdefense.glutils as glutils


class PhraseText(Text):
    """Class for displaying text for a phrase.

    This is text associated with a position in the (3D) game world, but
    projected so that it appears the same size regardless of depth."""
    def __init__(self, app, cam, font, text, x, y, height,
                 align=Text.Align.left):
        super().__init__(font, text, x, y, height, align)

        self._shader = glutils.ShaderInstance(
            app, 'phrase_text.vs', 'phrase_text.fs',
            [('transMatrix', GL.GL_FLOAT_MAT4, cam.trans_matrix_as_array()),
             ('origin', GL.GL_FLOAT_VEC3, None),
             ('screenDimensions', GL.GL_FLOAT_VEC2,
              [app.window_width, app.window_height]),
             ('texUnit', GL.GL_INT, 0),
             ('inColour', GL.GL_FLOAT_VEC3, [1, 1, 1])])

    def draw(self, x, y, z, typedchars):
        """Draw the text."""
        self._shader.set_uniform('origin', [x, y, z], download=False)

        GL.glDisable(GL.GL_DEPTH_TEST)
        with self._shader.use(), self._vao.bind(), self._font.bind():
            self._shader.set_uniform('inColour', [1, 0, 0])
            for i in range(len(self._text)):
                if i == typedchars:
                    self._shader.set_uniform('inColour', [1, 1, 1])
                GL.glDrawArrays(GL.GL_TRIANGLE_STRIP, i * 4, 4)
        GL.glEnable(GL.GL_DEPTH_TEST)


class Phrase(object):
    """Class representing an in-game phrase."""

    def __init__(self, app, cam, phrase):
        font = app.resources.load_font('menufont.fnt')
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
