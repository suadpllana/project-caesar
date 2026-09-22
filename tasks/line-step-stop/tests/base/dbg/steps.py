from dbg import frames


class Engine:
    def __init__(self, img, link, locs):
        self.img = img
        self.link = link
        self.locs = locs
        self.hid = 0

    def run(self):
        if self.link.pc() in self.locs:
            return "hit"
        return self.cont()

    def cont(self):
        while True:
            pc = self.link.step()
            if pc is None:
                return None
            if pc in self.locs:
                return "hit"

    def step(self):
        return self._line(True)

    def next(self):
        return self._line(False)

    def finish(self):
        depth = len(self.link.stack())
        while True:
            pc = self.link.step()
            if pc is None:
                return None
            if pc in self.locs:
                return "hit"
            if len(self.link.stack()) < depth:
                return "done"

    def _line(self, into):
        pc = self.link.pc()
        depth = len(self.link.stack())
        line = frames.line_at(self.img, pc)
        while True:
            pc = self.link.step()
            if pc is None:
                return None
            if pc in self.locs:
                return "hit"
            d = len(self.link.stack())
            if d > depth:
                if into:
                    return "step"
                continue
            depth = d
            r = frames.row_at(self.img, pc)
            if r is not None and r.at == pc and r.stmt and r.line and r.line != line:
                return "step"
