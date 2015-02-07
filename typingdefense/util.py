"""Various utility classes and functions."""
import math


class Colour(object):

    """Colour class, representing both RGB+A and HSV+A.

    RGB values range from 0-1.
    H is from 0-360, S and V range from 0-1.
    """

    def __init__(self, r=1, g=1, b=1, a=1):
        self.r = r
        self.g = g
        self.b = b
        self.a = a

    @property
    def h(self):
        h, _, _ = Colour._rgb_to_hsv(self.r, self.g, self.b)
        return h

    @h.setter
    def h(self, h):
        self.r, self.b, self.g = Colour._hsv_to_rgb(h, self.s, self.v)

    @property
    def s(self):
        _, s, _ = Colour._rgb_to_hsv(self.r, self.g, self.b)
        return s

    @s.setter
    def s(self, s):
        self.r, self.b, self.g = Colour._hsv_to_rgb(self.h, s, self.v)

    @property
    def v(self):
        _, _, v = Colour._rgb_to_hsv(self.r, self.g, self.b)
        return v

    @v.setter
    def v(self, v):
        self.r, self.b, self.g = Colour._hsv_to_rgb(self.h, self.s, v)

    @staticmethod
    def _rgb_to_hsv(r, g, b):
        min_colour = min(r, g, b)
        max_colour = max(r, g, b)
        delta = max_colour - min_colour

        if max_colour == 0:
            # Black
            return (0, 0, 0)

        s = delta/ max_colour
        v = max_colour

        if r == max_colour:
            # Between yellow and magenta
            h = (g - b) / delta
        elif g == max_colour:
            # Between cyan and yellow
            h = 2 + (b - r) / delta
        else:
            # Between magenta and cyan
            h = 4 + (r - g) / delta

        h *= 60
        if h < 0:
            h += 360

        return (h, s, v)

    @staticmethod
    def _hsv_to_rgb(h, s, v):
        if s == 0:
            # Grey
            return (v, v, v)

        i = math.floor(h)
        f = (h / 60) - i
        p = v * (1 - s)
        q = v * (1 - s * f)
        t = v * (1 - s * (1-f))

        if i == 0:
            return (v, t, p)
        elif i == 1:
            return (q, v, p)
        elif i == 2:
            return (p, v, t)
        elif i == 3:
            return (p, q, v)
        elif i == 4:
            return (t, p, v)
        else:
            return (v, p, q)

    @classmethod
    def from_hsv(cls, h, s, v, a=1):
        r, g, b = cls._hsv_to_rgb(h, s, v)
        return cls(r, g, b, a)

    @classmethod
    def from_white(cls, a=1):
        return cls(1, 1, 1, a)

    @classmethod
    def from_red(cls, a=1):
        return cls(1, 0, 0, a)

    @classmethod
    def from_blue(cls, a=1):
        return cls(0, 1, 0, a)

    @classmethod
    def from_green(cls, a=1):
        return cls(0, 0, 1, a)

    @classmethod
    def from_black(cls, a=1):
        return cls(0, 0, 0, a)