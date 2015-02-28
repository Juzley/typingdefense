"""Various OpenGL utility classes."""
import math
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

    def __del__(self):
        # TODO: Work out how to call this
        # GL.glDeleteVertexArrays(1, self._id)
        pass

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

    def __del__(self):
        # TODO: Work out how to call this
        # GL.glDeleteBuffers(1, self._id)
        pass

    def bind(self):
        """Bind the vertex buffer.

        This is not a context manager as we often want to leave the buffer
        bound under a VAO.
        """
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self._id)


class ShaderInstance(object):
    class _CtxMgr(object):
        def __enter__(self):
            pass

        def __exit__(self, ex_type, ex_value, traceback):
            GL.glUseProgram(0)

    def __init__(self, app, vertex_shader, fragment_shader, uniforms):
        self._program = app.resources.load_shader_program(vertex_shader,
                                                          fragment_shader)
        self._uniforms = {}
        for uniform in uniforms:
            self._uniform_cache_add(uniform[0], uniform[1], uniform[2])

    def _uniform_cache_add(self, name, gl_type, value):
        self._uniforms[name] = (self._program.uniform(name), gl_type, value)

    def _dl_uniform(self, info):
        """Download a uniform value to the shader."""
        uniform, gl_type, value = info

        if gl_type == GL.GL_FLOAT_VEC2:
            GL.glUniform2f(uniform, value[0], value[1])
        elif gl_type == GL.GL_FLOAT_VEC4:
            GL.glUniform4f(uniform, value[0], value[1], value[2], value[3])
        elif gl_type == GL.GL_FLOAT_MAT4:
            GL.glUniformMatrix4fv(uniform, 1, GL.GL_TRUE, value)

    def set_uniform(self, name, value=None, download=True):
        """Set a uniform, optionally updating its value first.

        The shader must be bound before calling this method, if the value is
        to be downloaded."""
        if value is not None:
            self._uniforms[name] = (self._uniforms[name][0],
                                    self._uniforms[name][1],
                                    value)
        if download:
            self._dl_uniform(self._uniforms[name])

    def use(self, download_uniforms=True):
        self._program.use()
        if download_uniforms:
            for uniform_info in self._uniforms.values():
                self._dl_uniform(uniform_info)
        return ShaderInstance._CtxMgr()


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

        return pixel[0][0]


class Hex(object):
    def __init__(self, coords, size, depth, stacks=1):
        self._stacks = stacks

        # The top layer of the tile is drawn with a line loop.
        # The vertical sections are drawn with lines.
        all_verts = []
        for s in range(self._stacks):
            top_verts, vert_verts = ([], [])
            for i in range(6):
                z = coords.z + depth * s
                px = coords.x + size * math.sin((2 * math.pi / 6) * (5 - i))
                py = coords.y + size * math.cos((2 * math.pi / 6) * (5 - i))
                top_verts.extend([px, py, z + depth])

                px = coords.x + size * math.sin((2 * math.pi / 6) * i)
                py = coords.y + size * math.cos((2 * math.pi / 6) * i)
                vert_verts.extend([px, py, z, px, py, z + depth])
            all_verts.extend(top_verts + vert_verts)

        verts = numpy.array(all_verts, numpy.float32)

        self._vao = VertexArray()
        self._vbo = VertexBuffer()
        with self._vao.bind():
            self._vbo.bind()
            GL.glBufferData(GL.GL_ARRAY_BUFFER, verts.nbytes, verts,
                            GL.GL_STATIC_DRAW)
            GL.glEnableVertexAttribArray(0)
            GL.glVertexAttribPointer(0, 3, GL.GL_FLOAT, GL.GL_FALSE, 0, None)

    def draw_faces(self):
        with self._vao.bind():
            for s in range(self._stacks):
                GL.glDrawArrays(GL.GL_TRIANGLE_FAN, s * 18, 6)
                GL.glDrawArrays(GL.GL_TRIANGLE_STRIP, 6 + s * 18, 12)

    def draw_outline(self):
        with self._vao.bind():
            for s in range(self._stacks):
                GL.glDrawArrays(GL.GL_LINE_LOOP, s * 18, 6)
                GL.glDrawArrays(GL.GL_LINES, 6 + s * 18, 12)

    def draw(self, faces=True, outline=True):
        if outline:
            self.draw_outline()
        if faces:
            self.draw_faces()
