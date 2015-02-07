import sdl2
import sdl2.ext
import ctypes
import collections
from OpenGL import GL
from OpenGL.GL import shaders

# TODO: contextmanagers?

class Font(object):
    def __init__(self, filename):
        with open(filename, 'rb') as f:
            ex = RuntimeError("Invalid font file {}".format(filename))
            if f.read(4) != "FONT":
                raise ex

            texture_name_length = int.from_bytes(f.read(4), byteorder='little')
            if texture_name_length < 0:
                raise ex

            self._texture = Texture(f.read(texture_name_length).decode())

            # Skip the two bytes of image height and width, which we get from
            # the image itself.
            f.seek(8, 1)

            self._charheight = int.from_bytes(f.read(4), byteorder='little')
            if self._charheight < 0:
                raise ex

            self._chars = {}
            charinfo = collections.namedtuple('CharInfo', ['x', 'y', 'width'])
            c = f.read(1).decode()
            while len(c):
                self._chars[c] = charinfo(
                    int.from_bytes(f.read(4), byteorder='little'),
                    int.from_bytes(f.read(4), byteorder='little'),
                    int.from_bytes(f.read(4), byteorder='little'))
                c = f.read(1).decode()


class Texture(object):
    def __init__(self, filename):
        self.filename = filename
        image = sdl2.ext.load_image(filename)

        # TODO: Need to sort this
        #if sdl2.SDL_ISPIXELFORMAT_ALPHA(ctypes.uint_32(image.format)):
        pixel_format = GL.GL_RGB
        #else:
        #    pixel_format = GL.GL_RGB

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


class Shader(object):
    def __init__(self, filename, shader_type):
        self.shader_type = shader_type
        self.filename = filename
        with open(self.filename) as f:
            contents = f.read()
            self.shader = shaders.compileShader(contents, shader_type)


class ShaderProgram(object):
    def __init__(self, vertex_shader, fragment_shader):
        self.program = shaders.compileProgram(vertex_shader.shader,
                                              fragment_shader.shader)

    def use(self):
        GL.glUseProgram(self.program)

    def uniform(self, name):
        return GL.glGetUniformLocation(self.program, name)


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
        if (vs_path, fs_path)  not in self._shader_programs:
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
