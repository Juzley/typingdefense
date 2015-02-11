class Vector(object):
    def __init__(self, *args):
        if len(args) == 0:
            self.values = [0, 0]
        else:
            self.values = args

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
