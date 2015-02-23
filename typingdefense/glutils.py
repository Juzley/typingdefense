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

    def __del__(self):
        GL.glDeleteVertexArray(self._id)

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
        GL.glDeleteBuffers(self._id)

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

        if gl_type == GL.GL_FLOAT_VEC4:
            GL.glUniform4f(uniform,
                            value[0], value[1], value[2], value[3])
        elif gl_type == GL.GL_FLOAT_MAT4:
            GL.glUniformMatrix4fv(uniform, 1, GL.GL_TRUE, value)

    def set_uniform(self, name, value=None, download=True):
        """Set a uniform, optionally updating its value first.

        The shader must be bound before calling this method."""
        if value:
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
