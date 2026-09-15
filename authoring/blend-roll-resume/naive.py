"""A brute-force correct engine, written straight from the contract, draw by draw.

Used only for authoring cross-checks: it is what the rules say with nothing clever in it, so a
disagreement with the reference or with the sealed model is a real disagreement. It is also the
shape of the `slow` cheat, which is exactly correct and cannot finish the wide family.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tasks" / "blend-roll-resume"
                      / "environment" / "app_src"))

from mix import perm  # noqa: E402


class Sim:

    def __init__(self):
        self.seed = 0
        self.names = []
        self.size = {}
        self.weight = {}
        self.cap = {}
        self.live = []
        self.epoch = {}
        self.cur = {}
        self.cnt = {}
        self.step = 0
        self.cfg = None
        self.mark = None
        self.out = []

    # -- manifest ------------------------------------------------------------------
    def rebase(self):
        for name in self.live:
            self.cnt[name] = 0

    def sig(self):
        return tuple(self.live), tuple(self.weight[n] for n in self.live)

    def add(self, name, n, w, cap):
        self.names.append(name)
        self.size[name] = n
        self.weight[name] = w
        self.cap[name] = cap
        self.live.append(name)
        self.epoch[name] = 0
        self.cur[name] = 0
        self.cnt[name] = 0
        self.rebase()

    # -- one draw ------------------------------------------------------------------
    def who(self):
        best = None
        for name in self.live:
            if best is None:
                best = name
            elif self.cnt[name] * self.weight[best] < self.cnt[best] * self.weight[name]:
                best = name
        return best

    def take(self, name):
        row = perm.order(self.seed, self.names.index(name), self.epoch[name], self.size[name])
        got = row[self.cur[name]]
        self.cnt[name] += 1
        self.cur[name] += 1
        if self.cur[name] == self.size[name]:
            self.cur[name] = 0
            self.epoch[name] += 1
        return got

    def spent(self, name):
        return self.cap[name] and self.epoch[name] >= self.cap[name]

    def draw(self):
        name = self.who()
        got = self.take(name)
        gone = self.spent(name)
        return name, got, gone

    # -- ops -----------------------------------------------------------------------
    def ex(self, line):
        p = line.split()
        kind = p[0]
        if kind == "seed":
            self.seed = int(p[1])
        elif kind == "src":
            self.add(p[1], int(p[2]), int(p[3]), int(p[4]))
        elif kind == "wt":
            self.weight[p[1]] = int(p[2])
            self.rebase()
        elif kind == "run":
            self.cfg = (int(p[1]), int(p[2]), int(p[3]))
        elif kind == "save":
            self.mark = {"step": self.step, "epoch": dict(self.epoch), "cur": dict(self.cur),
                         "cnt": dict(self.cnt), "sig": self.sig()}
        elif kind == "stop":
            m = self.mark
            self.step = m["step"]
            for name in m["epoch"]:
                self.epoch[name] = m["epoch"][name]
                self.cur[name] = m["cur"][name]
                self.cnt[name] = m["cnt"][name]
            if self.sig() != m["sig"]:
                self.rebase()
            self.cfg = None
        elif kind == "go":
            ranks, micro, accum = self.cfg
            wide = ranks * micro * accum
            for _ in range(int(p[1])):
                for pos in range(wide):
                    name, _got, gone = self.draw()
                    if gone:
                        self.out.append("done %s %d %d" % (name, self.step, pos))
                        self.live.remove(name)
                        self.rebase()
                self.step += 1
        elif kind == "feed":
            ranks, micro, accum = self.cfg
            rank, slot = int(p[1]), int(p[2])
            lo = (slot * ranks + rank) * micro
            hi = lo + micro
            keep = (dict(self.epoch), dict(self.cur), dict(self.cnt), list(self.live))
            got = []
            for pos in range(hi):
                name, one, gone = self.draw()
                if pos >= lo:
                    got.append("%s:%d" % (name, one))
                if gone:
                    self.live.remove(name)
                    self.rebase()
            self.epoch, self.cur, self.cnt, self.live = keep
            self.out.append("feed %d %d %s" % (rank, slot, " ".join(got)))
        elif kind == "at":
            name = p[1]
            if name in self.live:
                self.out.append("at %s %d %d" % (name, self.epoch[name], self.cur[name]))
            else:
                self.out.append("at %s out" % name)
        else:
            raise ValueError(kind)


def expect(lines):
    sim = Sim()
    for line in lines:
        sim.ex(line)
    return sim.out
