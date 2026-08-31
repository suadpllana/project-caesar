from collections import deque

from kern import knot, pick, stop, wake
from kern.fib import Fib
from kern.gd import Bd, Gd, busy, chain, inner

CAP = 200000


class Spin(Exception):
    pass


class Loop:
    def __init__(self, progs, sink):
        self.pr = progs
        self.sink = sink
        self.t = 0
        self.rq = deque()
        self.fs = []
        self.nid = 0
        self.gm = {}
        self.n = 0

    def ev(self, *row):
        self.sink((self.t,) + row)

    def new(self, pid, inh, home):
        f = Fib(self.nid, pid, self.pr[pid], inh, home)
        self.nid += 1
        self.fs.append(f)
        self.ev("go", f.fid, pid)
        return f

    def mark(self, g, why):
        if g.hit:
            return
        g.hit = True
        g.src = why
        self.ev("mk", g.lbl, why)
        self.rouse()

    def rouse(self):
        for f in self.fs:
            if f.st == 1 and f.wake is not None:
                if wake.rouse(f, chain(f)):
                    f.wake = None
                    f.st = 0
                    self.rq.append(f)

    def ask(self, f):
        ch = chain(f)
        g = pick.pick(f, ch)
        if g is None:
            return None
        for h in ch:
            if h is g:
                return g
        raise Spin("stray")

    def hurl(self, f, box):
        if f.pend is None:
            f.pend = box
        else:
            f.pend = stop.blend(f.pend, box)
        if f.deep():
            f.fr.pop()

    def cut(self, f, g):
        self.ev("ct", f.fid, g.lbl)
        self.hurl(f, ("cut", g))

    def step(self, f):
        self.ev("on", f.fid)
        while True:
            self.n += 1
            if self.n > CAP:
                raise Spin("cap")
            fr = f.fr[-1]
            if fr[1] >= len(fr[0]):
                if f.deep():
                    f.fr.pop()
                    continue
                if f.pend is None:
                    self.fini(f)
                    return
            if f.pend is not None and not f.deep():
                if self.shed(f):
                    return
                continue
            fr = f.fr[-1]
            if fr[1] >= len(fr[0]):
                continue
            if self.exec(f, fr[0][fr[1]]):
                return

    def exec(self, f, op):
        k = op[0]
        fr = f.fr[-1]
        if k == "S":
            f.toks.append(op[1])
            self.ev("tk", f.fid, op[1])
            fr[1] += 1
            return False
        if k == "P":
            g = self.ask(f)
            if g is not None:
                fr[1] += 1
                self.cut(f, g)
                return False
            fr[1] += 1
            f.st = 1
            self.rq.append(f)
            return True
        if k == "W":
            if not f.warm:
                g = self.ask(f)
                if g is not None:
                    fr[1] += 1
                    self.cut(f, g)
                    return False
                if op[1] <= 0:
                    fr[1] += 1
                    f.st = 1
                    self.rq.append(f)
                    return True
                f.warm = True
                f.wake = self.t + op[1]
                f.st = 1
                return True
            f.warm = False
            f.wake = None
            g = self.ask(f)
            if g is not None:
                fr[1] += 1
                self.cut(f, g)
                return False
            fr[1] += 1
            return False
        if k == "H":
            g = inner(f)
            if g is not None:
                g.sh = bool(op[1])
            fr[1] += 1
            return False
        if k == "M":
            g = self.gm.get(op[1])
            if g is not None:
                self.mark(g, "op")
            fr[1] += 1
            return False
        if k == "F":
            fr[1] += 1
            self.hurl(f, ("err", f.fid))
            return False
        if k == "A":
            g = inner(f)
            if g is not None:
                g.cl = op[1]
            fr[1] += 1
            return False
        if k == "G":
            g = Gd(op[1], None if op[2] < 0 else self.t + op[2], bool(op[3]),
                   f.fid, op[4], "g")
            f.bl.append(("g", g))
            self.gm[op[1]] = g
            self.ev("op", f.fid, op[1])
            fr[1] += 1
            if g.dl is not None and g.dl <= self.t:
                self.mark(g, "dl")
            return False
        if k == "E":
            g = f.bl.pop()[1]
            self.gm.pop(g.lbl, None)
            self.ev("cl", f.fid, g.lbl, "ok")
            fr[1] += 1
            self.after(f, g)
            return False
        if k == "B":
            g = Gd(op[1], None, False, f.fid, op[2], "b")
            bd = Bd(op[1], f, g, op[2], None)
            f.bl.append(("b", bd))
            self.gm[op[1]] = g
            bd.inh = chain(f)
            self.ev("bo", f.fid, op[1])
            fr[1] += 1
            return False
        if k == "X":
            return self.shut(f, f.bl[-1][1])
        if k == "N":
            bd = None
            for e in reversed(f.bl):
                if e[0] == "b":
                    bd = e[1]
                    break
            if bd is not None:
                kid = self.new(op[1], list(bd.inh), bd)
                bd.kids.append(kid)
                self.ev("sp", f.fid, kid.fid)
                self.rq.append(kid)
            fr[1] += 1
            return False
        raise Spin(k)

    def after(self, f, g):
        if g.cl:
            self.ev("cu", f.fid, g.lbl)
            f.fr.append([g.cl, 0])

    def shut(self, f, bd):
        left = busy(bd)
        if left:
            g = self.ask(f)
            if g is not None and knot.wait(bd, g, left) == "cut":
                self.cut(f, g)
                return False
            f.st = 1
            f.hold = bd
            return True
        g = self.ask(f)
        res = knot.shut(bd, chain(f), g)
        f.bl.pop()
        self.gm.pop(bd.gd.lbl, None)
        self.ev("bc", f.fid, bd.lbl, res[0] if res else "ok")
        f.fr[-1][1] = bd.end + 1
        if res is not None:
            if res[0] == "cut":
                self.cut(f, res[1])
            else:
                self.hurl(f, ("bun", tuple(res[1])))
        self.after(f, bd.gd)
        return False

    def shed(self, f):
        if not f.bl:
            self.fini(f)
            return True
        kind, obj = f.bl[-1]
        if kind == "b":
            left = busy(obj)
            if left:
                if knot.snag(obj, left):
                    self.mark(obj.gd, "op")
                f.st = 1
                f.hold = obj
                return True
            f.bl.pop()
            self.gm.pop(obj.gd.lbl, None)
            self.ev("bc", f.fid, obj.lbl, f.pend[0])
            self.after(f, obj.gd)
            return False
        g = obj
        f.bl.pop()
        self.gm.pop(g.lbl, None)
        self.ev("cl", f.fid, g.lbl, f.pend[0])
        if f.pend[0] == "cut" and stop.stops(g, chain(f), f.pend[1]):
            f.pend = None
            f.fr[-1][1] = g.end + 1
        self.after(f, g)
        return False

    def fini(self, f):
        f.st = 2
        f.fin = self.t
        box = f.pend
        if box is None:
            self.ev("en", f.fid, "ok", 0)
        elif box[0] == "cut":
            self.ev("en", f.fid, "cut", box[1].lbl)
        elif box[0] == "err":
            self.ev("en", f.fid, "err", box[1])
        else:
            self.ev("en", f.fid, "bun", list(box[1]))
        bd = f.home
        if bd is None:
            return
        if box is not None and box[0] in ("err", "bun"):
            pay = [box[1]] if box[0] == "err" else list(box[1])
            if knot.reap(bd, f.fid, self.t, pay):
                self.mark(bd.gd, "op")
        if not busy(bd) and bd.own.hold is bd:
            bd.own.hold = None
            bd.own.st = 0
            self.rq.append(bd.own)

    def tick(self):
        cand = []
        for f in self.fs:
            if f.st == 1 and f.wake is not None:
                cand.append(f.wake)
        for g in self.gm.values():
            if g.dl is not None and not g.hit:
                cand.append(g.dl)
        if not cand:
            return False
        nt = max(min(cand), self.t)
        self.t = nt
        for lbl in sorted(self.gm):
            g = self.gm.get(lbl)
            if g is not None and g.dl is not None and not g.hit and g.dl <= self.t:
                self.mark(g, "dl")
        for f in self.fs:
            if f.st == 1 and f.wake is not None and f.wake <= self.t:
                f.wake = None
                f.st = 0
                self.rq.append(f)
        return True

    def run(self, root):
        f = self.new(root, [], None)
        self.rq.append(f)
        while True:
            while self.rq:
                nx = self.rq.popleft()
                if nx.st == 2:
                    continue
                nx.st = 0
                self.step(nx)
            if not self.tick():
                break
        return f
