class Sealer:
    def __init__(self, wm):
        self.wm = wm
        self.sealed = {}
        self.revised = 0

    def mark(self, g, kind, w):
        self.sealed[(g, kind)] = w
