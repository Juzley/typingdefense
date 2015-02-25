"""Vector module."""
import math


class Vector(object):
    """Vector class."""

    def __init__(self, *args):
        if len(args) == 0:
            self.values = [0, 0]
        else:
            self.values = args

    def __str__(self):
        return str(self.values)

    def __add__(self, other):
        if len(self.values) != len(other.values):
            raise ArithmeticError('Adding vectors of different sizes')
        return Vector(*[a + b for (a, b) in zip(self.values, other.values)])

    def __iadd__(self, other):
        if len(self.values) != len(other.values):
            raise ArithmeticError('Adding vectors of different sizes')
        self.values = [a + b for (a, b) in zip(self.values, other.values)]
        return self

    def __sub__(self, other):
        if len(self.values) != len(other.values):
            raise ArithmeticError('Adding vectors of different sizes')
        return Vector(*[a - b for (a, b) in zip(self.values, other.values)])

    def __isub__(self, other):
        if len(self.values) != len(other.values):
            raise ArithmeticError('Adding vectors of different sizes')
        self.values = [a - b for (a, b) in zip(self.values, other.values)]
        return self

    def __mul__(self, other):
        return Vector(*[v * other for v in self.values])

    def __imul__(self, other):
        self.values = [v * other for v in self.values]
        return self

    def __div__(self, other):
        return Vector(*[v / other for v in self.values])

    def __idiv__(self, other):
        self.values = [v / other for v in self.values]
        return self

    @property
    def x(self):
        return self.values[0]

    @x.setter
    def x(self, val):
        self.values[0] = val

    @property
    def y(self):
        return self.values[1]

    @y.setter
    def y(self, val):
        self.values[1] = val

    @property
    def z(self):
        return self.values[2]

    @z.setter
    def z(self, val):
        self.values[2] = val

    @property
    def w(self):
        return self.values[3]

    @w.setter
    def w(self, val):
        self.values[3] = val

    @property
    def q(self):
        return self.values[0]

    @q.setter
    def q(self, val):
        self.values[0] = val

    @property
    def r(self):
        return self.values[1]

    @r.setter
    def r(self, val):
        self.values[1] = val

    @property
    def magnitude(self):
        s = 0
        for v in self.values:
            s += v**2
        return math.sqrt(s)

    def normalize(self):
        m = self.magnitude
        self.values = [v / m for v in self.values]
