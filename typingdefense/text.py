"""Text using texture-map fonts."""
import ctypes
import numpy
import typingdefense.glutils as glutils
import OpenGL.GL as GL
from enum import Enum, unique


class Text(object):
    """Class for drawing texture-mapped text."""

    @unique
    class Align(Enum):
        """Enumeration of text alignments."""
        left = 1
        center = 2
        right = 3

    def __init__(self, font, text, x, y, height, align=Align.left):
        self._font = font
        self._vao = glutils.VertexArray()
        self._vbo = glutils.VertexBuffer()
        self.height = height
        self.width = 0
        self._align = align
        self._x = x
        self._y = y
        self._text = None
        self.text = text

    @property
    def text(self):
        """Get the text associated with the instance."""
        return self._text

    @text.setter
    def text(self, text):
        """Update the text associated with the instance.

        This updates the vertex buffers etc.
        """
        if text != self._text:
            self._text = text

            x, y = (self._x, self._y)

            # If the text isn't left-aligned, calculate how much we need to
            # adjust the x coordinate by
            self.width = 0
            for c in self._text:
                self.width += self._font.char_width(c, self.height)

            if self._align == Text.Align.center:
                x -= self.width / 2
            elif self._align == Text.Align.right:
                x -= self.width

            data = []
            for c in self._text:
                width = self._font.char_width(c, self.height)
                tc = self._font.texcoords(c)

                data += [x, y, tc[0], tc[1],                        # Bot Left
                         x + width, y, tc[2], tc[3],                # Bot Right
                         x, y + self.height, tc[4], tc[5],          # Top Left
                         x + width, y + self.height, tc[6], tc[7]]  # Top Right
                x += width

            with self._vao.bind():
                self._vbo.bind()
                data_array = numpy.array(data, numpy.float32)
                GL.glBufferData(GL.GL_ARRAY_BUFFER,
                                data_array.nbytes, data_array,
                                GL.GL_STATIC_DRAW)
                GL.glEnableVertexAttribArray(0)
                GL.glVertexAttribPointer(0, 2, GL.GL_FLOAT, GL.GL_FALSE, 16,
                                         None)
                GL.glEnableVertexAttribArray(1)
                GL.glVertexAttribPointer(1, 2, GL.GL_FLOAT, GL.GL_FALSE, 16,
                                         ctypes.c_void_p(8))

    def draw(self, text=None):
        """Draw the text."""
        if text is not None and text != self._text:
            self.text = text

        with self._vao.bind(), self._font.bind():
            for i in range(len(self._text)):
                GL.glDrawArrays(GL.GL_TRIANGLE_STRIP, i * 4, 4)


class Text2D(Text):
    """2D Text, used for HUD drawing."""
    def __init__(self, app, font, text, x, y, height, align=Text.Align.left):
        super().__init__(font, text, x, y, height, align)
        self._shader = glutils.ShaderInstance(
            app, 'ortho.vs', 'texture.fs',
            [('screenDimensions', GL.GL_FLOAT_VEC2,
              [app.window_width, app.window_height]),
             ('texUnit', GL.GL_INT, 0)])

    def draw(self, text=None):
        """Draw the text."""
        with self._shader.use():
            super().draw(text)
