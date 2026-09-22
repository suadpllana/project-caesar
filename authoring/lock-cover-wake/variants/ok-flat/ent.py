from . import mode


class Item:
    __slots__ = ("tid", "seq", "m", "conv", "cont")

    def __init__(self, tid, seq, m, conv, cont):
        self.tid = tid
        self.seq = seq
        self.m = m
        self.conv = conv
        self.cont = cont


class Ent:
    """Holders as a flat list of pairs, and one queue carrying a conversion flag."""

    __slots__ = ("res", "hold", "line", "old", "count")

    def __init__(self, res):
        self.res = res
        self.hold = []
        self.line = []
        self.old = None
        self.count = [0, 0, 0, 0, 0]

    # --- the granted side ------------------------------------------------------

    @property
    def held(self):
        return dict(self.hold)

    def put(self, tid, m):
        for pair in self.hold:
            if pair[0] == tid:
                if pair[1] != m:
                    self.count[mode.MODES.index(pair[1])] -= 1
                    self.count[mode.MODES.index(m)] += 1
                    pair[1] = m
                return
        self.hold.append([tid, m])
        self.count[mode.MODES.index(m)] += 1

    def lose(self, tid):
        for i, pair in enumerate(self.hold):
            if pair[0] == tid:
                self.count[mode.MODES.index(pair[1])] -= 1
                del self.hold[i]
                return

    def has(self, tid):
        for pair in self.hold:
            if pair[0] == tid:
                return True
        return False

    def holders(self):
        return [pair[0] for pair in self.hold]

    def hits_but(self, tid, m):
        mine = None
        for who, v in self.hold:
            if who == tid:
                mine = v
                break
        for bad in mode.BAD[m]:
            if self.count[mode.MODES.index(bad)] > (1 if mine == bad else 0):
                return True
        return False

    def foes(self, tid, m):
        bad = mode.BAD[m]
        return [who for who, v in self.hold if who != tid and v in bad]

    # --- the waiting side ------------------------------------------------------

    def waiting(self):
        return bool(self.line)

    def head(self):
        for it in self.line:
            if it.conv:
                return it
        return self.line[0]

    def queued(self):
        return [it for it in self.line if it.conv] + [it for it in self.line if not it.conv]

    def convs(self):
        for it in self.line:
            if it.conv:
                return True
        return False

    def push(self, it):
        self.line.append(it)
        self.redo()

    def pop_head(self):
        it = self.head()
        self.line.remove(it)
        self.redo()
        return it

    def drop_wait(self, tid):
        for i, it in enumerate(self.line):
            if it.tid == tid:
                del self.line[i]
                self.redo()
                return it
        return None

    def redo(self):
        best = None
        for it in self.line:
            if best is None or it.seq < best:
                best = it.seq
        self.old = best
