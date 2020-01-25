from definitions import *
class Shape(object):
    def __init__(self, x, y, shape):
        self.x = x
        self.y = y
        self.shape = shape
        self.shapeIdx = shapes.index(shape)
        self.color = shape_colors[self.shapeIdx]
        self.rotation = 0

    def __copy__(self):
        cp = Shape(self.x, self.y, self.shape)
        cp.rotation = self.rotation
        cp.shapeIdx = self.shapeIdx
        return cp
