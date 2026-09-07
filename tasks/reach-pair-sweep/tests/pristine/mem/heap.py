NURSERY = "n"
OLD = "o"

PROMOTE_AGE = 2


class Obj:
    __slots__ = ("flds", "fin", "space", "age", "pins", "ser")

    def __init__(self, fin, ser):
        self.flds = {}
        self.fin = fin
        self.space = NURSERY
        self.age = 0
        self.pins = 0
        self.ser = ser


class Heap:
    __slots__ = ("objs", "frames", "globs", "handles", "pairs", "weak", "queue", "done",
                 "rset", "young", "stamp")

    def __init__(self):
        self.objs = {}
        self.frames = [{}]
        self.globs = {}
        self.handles = []
        self.pairs = []
        self.weak = {}
        self.queue = []
        self.done = set()
        self.rset = set()
        self.young = set()
        self.stamp = 0
