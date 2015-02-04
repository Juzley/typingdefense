import numpy
from OpenGL import GL


class Level(object):
    def __init__(self, app, game):
        self._cam = game.cam
        self._vao = GL.glGenVertexArrays(1)
        self._vbo = GL.glGenBuffers(1)

        self._shader = app.resources.load_shader_program("test.vs",
                                                         "test.fs")
        self._transmatrix_uniform = self._shader.uniform('transMatrix')

        GL.glBindVertexArray(self._vao)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self._vbo)

        verts = numpy.array([0, 0, 0])
        GL.glBufferData(GL.GL_ARRAY_BUFFER, verts.nbytes, verts,
                        GL.GL_STATIC_DRAW)
        GL.glEnableVertexAttribArray(0)
        GL.glVertexAttribPointer(0, 3, GL.GL_FLOAT, GL.GL_FALSE, 0, None)
        GL.glBindVertexArray(0)

    def draw(self):
        self._shader.use()
        GL.glUniformMatrix4fv(self._transmatrix_uniform, 1, GL.GL_TRUE,
                              self._cam.trans_matrix_as_array())
        GL.glBindVertexArray(self._vao)
        GL.glDrawArrays(GL.GL_TRIANGLE_STRIP, 0, 1)

        GL.glBindVertexArray(0)
        GL.glUseProgram(0)
