"""Independent per-slot model of shard-spend-carry. Deliberately the dumbest reading of the
contract: every slot is a separate cell and every rank walks every slot it owns."""


class Run:
    def __init__(self):
        self.n = {}          # name -> slot count
        self.v = {}          # name -> list of values
        self.m = {}
        self.g = {}
        self.live = {}
        self.since = {}
        self.order = []
        self.map = []
        self.ws = 1
        self.bud = 0
        self.dirty = True
        self.ckpt = {}
        self.clock = 0
        self.out = []

    def flat(self):
        cells = []
        for name in self.map:
            for i in range(self.n[name]):
                cells.append((name, i))
        return cells

    def relay(self):
        keep = [x for x in self.map if self.live[x]]
        for x in self.map:
            if not self.live[x]:
                self.m[x] = [0] * self.n[x]
        new = [x for x in self.order if self.live[x] and x not in self.map]
        new.sort(key=lambda x: self.since[x])
        self.map = keep + new
        self.dirty = False

    def run(self, lines):
        for line in lines:
            t = line.split()
            if not t:
                continue
            op = t[0]
            self.clock += 1
            if op == "par":
                name, n = t[1], int(t[2])
                self.n[name] = n
                self.v[name] = [0] * n
                self.m[name] = [0] * n
                self.g[name] = [0] * n
                self.live[name] = True
                self.since[name] = self.clock
                self.order.append(name)
                self.dirty = True
            elif op == "frz":
                self.live[t[1]] = False
                self.dirty = True
            elif op == "thw":
                self.live[t[1]] = True
                self.since[t[1]] = self.clock
                self.dirty = True
            elif op == "ws":
                self.ws = int(t[1])
                self.dirty = True
            elif op == "bud":
                self.bud = int(t[1])
            elif op == "grd":
                k = int(t[2])
                gs = self.g[t[1]]
                for i in range(len(gs)):
                    gs[i] += k
            elif op == "step":
                if self.dirty:
                    self.relay()
                cells = self.flat()
                total = len(cells)
                if total:
                    s = -(-total // self.ws)
                    for r in range(self.ws):
                        a = min(r * s, total)
                        b = min((r + 1) * s, total)
                        spent = 0
                        for k in range(a, b):
                            name, i = cells[k]
                            g = self.g[name][i]
                            if g == 0:
                                continue
                            if spent + abs(g) > self.bud:
                                break
                            spent += abs(g)
                            self.m[name][i] += g
                            self.v[name][i] -= self.m[name][i]
                            self.g[name][i] = 0
            elif op == "save":
                cells = self.flat()
                self.ckpt[t[1]] = (list(cells),
                                   [(self.v[nm][i], self.m[nm][i]) for nm, i in cells])
            elif op == "load":
                cells, vals = self.ckpt[t[1]]
                for (nm, i), (v, m) in zip(cells, vals):
                    self.v[nm][i] = v
                    self.m[nm][i] = m
            elif op == "own":
                r = int(t[1])
                cells = self.flat()
                total = len(cells)
                if total == 0 or r >= self.ws:
                    self.out.append("own %d none" % r)
                else:
                    s = -(-total // self.ws)
                    a = min(r * s, total)
                    b = min((r + 1) * s, total)
                    if a >= b:
                        self.out.append("own %d none" % r)
                    else:
                        nm, i = cells[a]
                        self.out.append("own %d %s %d" % (r, nm, i))
            elif op in ("val", "mom"):
                arr = (self.v if op == "val" else self.m)[t[1]]
                parts = []
                for x in arr:
                    if parts and parts[-1][1] == x:
                        parts[-1][0] += 1
                    else:
                        parts.append([1, x])
                self.out.append("%s %s %s" % (op, t[1],
                                              " ".join("%dx%d" % (c, v) for c, v in parts)))
            else:
                raise SystemExit("bad op %r" % op)
        return self.out


def expect(lines):
    return Run().run(list(lines))
