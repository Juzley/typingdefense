"""Various OpenGL utility classes."""
from OpenGL import GL
from contextlib import contextmanager


@contextmanager
def linewidth(width):
    GL.glLineWidth(width)
    try:
        yield
    finally:
        GL.glLineWidth(1)


class VertexArray(object):
    def __init__(self):
        self._id = GL.glGenVertexArrays(1)

    @contextmanager
    def bind(self):
        GL.glBindVertexArray(self._id)
        try:
            yield
        finally:
            GL.glBindVertexArray(0)


class VertexBuffer(object):
    def __init__(self):
        self._id = GL.glGenBuffers(1)

    def bind(self):
        """Bind the vertex buffer.

        This is not a context manager as we often want to leave the buffer
        bound under a VAO.
        """
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self._id)


class PickingTexture(object):
    def __init__(self, window_width, window_height):
        self._framebuf = GL.glGenFramebuffers(1)
        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, self._framebuf)

        self._picktex = GL.glGenTextures(1)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self._picktex)
        GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, GL.GL_RGBA32F,
                        window_width, window_height, 0, GL.GL_RGB, GL.GL_FLOAT,
                        None)
        GL.glFramebufferTexture2D(GL.GL_DRAW_FRAMEBUFFER,
                                  GL.GL_COLOR_ATTACHMENT0, GL.GL_TEXTURE_2D,
                                  self._picktex, 0)

        self._depthtex = GL.glGenTextures(1)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self._depthtex)
        GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, GL.GL_DEPTH_COMPONENT,
                        window_width, window_height, 0, GL.GL_DEPTH_COMPONENT,
                        GL.GL_FLOAT, None)
        GL.glFramebufferTexture2D(GL.GL_DRAW_FRAMEBUFFER,
                                  GL.GL_DEPTH_ATTACHMENT,
                                  GL.GL_TEXTURE_2D,
                                  self._depthtex, 0)

        GL.glReadBuffer(GL.GL_NONE)
        GL.glDrawBuffer(GL.GL_COLOR_ATTACHMENT0)

        # Restore the default framebuffer
        GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, 0)

    @contextmanager
    def enable(self):
        GL.glBindFramebuffer(GL.GL_DRAW_FRAMEBUFFER, self._framebuf)
        try:
            yield
        finally:
            GL.glBindFramebuffer(GL.GL_DRAW_FRAMEBUFFER, 0)

    def read(self, x, y):
        GL.glBindFramebuffer(GL.GL_READ_FRAMEBUFFER, self._framebuf)
        with self.enable():
            GL.glReadBuffer(GL.GL_COLOR_ATTACHMENT0)
            pixel = GL.glReadPixels(x, y, 1, 1, GL.GL_RGB, GL.GL_FLOAT)
            GL.glReadBuffer(GL.GL_NONE)

        return pixel
