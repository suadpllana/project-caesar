class Mx:
    __slots__ = ("id", "h", "w")

    def __init__(self, mid):
        self.id = mid
        self.h = 0
        self.w = []

    def __repr__(self):
        return "M(%d h=%d w=%s)" % (self.id, self.h, self.w)
