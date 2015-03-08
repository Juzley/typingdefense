"""Module containing classes for managing resources."""
import sdl2
import sdl2.ext
import ctypes
import collections
import os
from OpenGL import GL
from OpenGL.GL import shaders

# TODO: contextmanagers?


class Font(object):
    """Class representing texture-mapped fonts."""

    def __init__(self, filename):
        with open(filename, 'rb') as f:
            header = f.read(4).decode()
            if header != "FONT":
                raise RuntimeError(
                    "Invalid font file {}, bad header {}".format(filename,
                                                                 header))

            texture_name_length = int.from_bytes(f.read(4), byteorder='little')
            if texture_name_length < 0:
                raise RuntimeError(
                    "Invalid font file {}, bad texture name".format(filename))

            texture_name = f.read(texture_name_length).decode()
            texture_path = "{}/{}".format(os.path.dirname(filename),
                                          texture_name)
            self._texture = Texture(texture_path)

            # Skip the two bytes of image height and width, which we get from
            # the image itself.
            f.seek(8, 1)

            self._charheight = int.from_bytes(f.read(4), byteorder='little')
            if self._charheight < 0:
                raise RuntimeError(
                    "Invalid font file {}, bad char heigh".format(filename))

            self._chars = {}
            charinfo = collections.namedtuple('CharInfo', ['x', 'y', 'width'])
            c = f.read(1).decode()
            while len(c):
                self._chars[c] = charinfo(
                    int.from_bytes(f.read(4), byteorder='little'),
                    int.from_bytes(f.read(4), byteorder='little'),
                    int.from_bytes(f.read(4), byteorder='little'))
                c = f.read(1).decode()

    def bind(self):
        """Bind the texture for a font."""
        self._texture.bind()

    def char_width(self, c, h):
        """Return the width, in pixels, for a given character."""
        if c not in self._chars:
            return 0

        charinfo = self._chars[c]
        return charinfo.width * h / self._charheight

    def texcoords(self, c):
        """Return the texture coordinates for a given character.

        The coordinates are returned as an 8 element tuple containing the
        texture coordinates in the following order: bottom left, bottom right
        top left, top right.
        """
        if c not in self._chars:
            return [0, 0, 0, 0, 0, 0, 0, 0]

        charinfo = self._chars[c]
        x = charinfo.x / self._texture.width
        y = charinfo.y / self._texture.height
        w = charinfo.width / self._texture.width
        h = self._charheight / self._texture.height
        return [x,     y + h,  # Bottom Left
                x + w, y + h,  # Bottom Right
                x,     y,      # Top Left
                x + w, y]      # Top Right


class Texture(object):
    def __init__(self, filename):
        self.filename = filename
        image = sdl2.ext.load_image(filename)
        self._width = image.w
        self._height = image.h

        if sdl2.SDL_ISPIXELFORMAT_ALPHA(image.format.contents.format):
            pixel_format = GL.GL_RGBA
        else:
            pixel_format = GL.GL_RGB

        self._id = GL.glGenTextures(1)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self._id)
        GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, GL.GL_RGBA, image.w, image.h, 0,
                        pixel_format, GL.GL_UNSIGNED_BYTE,
                        ctypes.c_void_p(image.pixels))
        GL.glTexParameterf(GL.GL_TEXTURE_2D,
                           GL.GL_TEXTURE_MIN_FILTER,
                           GL.GL_LINEAR)
        GL.glTexParameterf(GL.GL_TEXTURE_2D,
                           GL.GL_TEXTURE_MAG_FILTER,
                           GL.GL_LINEAR)
        GL.glBindTexture(GL.GL_TEXTURE_2D, 0)

    def bind(self):
        GL.glBindTexture(GL.GL_TEXTURE_2D, self._id)

    @property
    def width(self):
        return self._width

    @property
    def height(self):
        return self._height


class Shader(object):
    def __init__(self, filename, shader_type):
        self.shader_type = shader_type
        self.filename = filename
        with open(self.filename) as f:
            contents = f.read()
            self.shader = shaders.compileShader(contents, shader_type)


class ShaderProgram(object):
    def __init__(self, vertex_shader, fragment_shader, uniforms=[]):
        self.program = shaders.compileProgram(vertex_shader.shader,
                                              fragment_shader.shader)
        self._uniforms = {}
        for uniform in uniforms:
            self._lookup_uniform(uniform)

    def _lookup_uniform(self, uniform):
        if uniform not in self._uniforms:
            self._uniforms[uniform] = GL.glGetUniformLocation(self.program,
                                                              uniform)

    def use(self):
        GL.glUseProgram(self.program)

    def uniform(self, name):
        self._lookup_uniform(name)
        return self._uniforms[name]


class Resources(object):
    def __init__(self, resource_path="", texture_path="", shader_path="",
                 font_path=""):
        self.resource_path = resource_path
        self.texture_path = texture_path
        self.shader_path = shader_path
        self.font_path = font_path
        self._textures = {}
        self._shaders = {}
        self._shader_programs = {}
        self._fonts = {}

    def _build_path(self, path, filename):
        return "/".join([self.resource_path, path, filename])

    def load_texture(self, filename):
        path = self._build_path(self.texture_path, filename)
        if path not in self._textures:
            self._textures[path] = Texture(path)

        return self._textures[path]

    def load_shader(self, filename, shader_type):
        path = self._build_path(self.shader_path, filename)
        if path not in self._shaders:
            self._shaders[path] = Shader(path, shader_type)

        return self._shaders[path]

    def load_shader_program(self, vs_filename, fs_filename):
        vs_path = self._build_path(self.shader_path, vs_filename)
        fs_path = self._build_path(self.shader_path, fs_filename)
        if (vs_path, fs_path) not in self._shader_programs:
            vs = self.load_shader(vs_filename, GL.GL_VERTEX_SHADER)
            fs = self.load_shader(fs_filename, GL.GL_FRAGMENT_SHADER)
            program = ShaderProgram(vs, fs)
            self._shader_programs[(vs_path, fs_path)] = program

        return self._shader_programs[(vs_path, fs_path)]

    def load_font(self, filename):
        path = self._build_path(self.font_path, filename)
        if path not in self._fonts:
            self._fonts[path] = Font(path)

        return self._fonts[path]
