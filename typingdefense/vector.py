class Vector(object):
    def __init__(self, *args):
        if len(args) == 0:
            self.values = [0, 0]
        else:
            self.values = args

    def __str__(self):
        return str(self.values)

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
