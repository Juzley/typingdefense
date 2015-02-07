import numpy
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
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self._id)

    def bind_and_set_data(self, data):
        self.bind()
        verts = numpy.array(data, numpy.float32)
        GL.glBufferData(GL.GL_ARRAY_BUFFER, verts.nbytes, verts,
                        GL.GL_STATIC_DRAW)




