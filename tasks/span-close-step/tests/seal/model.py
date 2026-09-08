"""The expected trace, derived independently of the reference solution.

Written from the contract, not from the shipped tree, and deliberately by a
different route at every point where the reference makes a structural choice:

* the token flow is materialised as one flat list with a cursor, so a step is a
  slice of it, where the reference keeps a queue and a policy-side count of how
  much of each open document it has consumed;
* settlement is decided by asking whether a document's *last* token lies inside
  the slice, where the reference asks whether the running count has reached the
  document's length;
* settlement order comes from the position of that last token in the flow, where
  the reference relies on occurrence keys being handed out in stream order;
* a checkpoint here is a deep copy of the whole simulation state, where the
  reference splits it into a stream half owned by the runtime and a trainer half
  the policy serialises through JSON.

The arithmetic of the objective, the schedule and the update is the contract
itself and is the same in both, as it must be.
"""
import copy
import math

FIELDS = 4


def feat(name, i):
    h = 2166136261
    for ch in name:
        h = ((h ^ ord(ch)) * 16777619) & 0xFFFFFFFF
    h = ((h ^ (i + 1)) * 16777619) & 0xFFFFFFFF
    h = (h ^ (h >> 13)) & 0xFFFFFFFF
    return [((h >> (7 * k)) % 9 - 4) / 4.0 for k in range(FIELDS)]


def fmt(x):
    if x == 0:
        x = 0.0
    return "%.6f" % x


class Sim:
    def __init__(self):
        self.cfg = {"lim": 8, "grp": 1, "wrk": 1, "seq": 1, "base": 0.1, "wu": 2,
                    "hl": 3, "mu": 0.5, "clip": 1.5, "bmax": 0.9, "thr": 1.2, "cap": 2}
        self.w = [0.25, -0.5, 0.75, 0.0]
        self.v = [0.0] * FIELDS
        self.ema = list(self.w)
        self.applied = 0
        self.docs = []          # (name, n, t, requeues_behind_it)
        self.flow = []          # (doc index, token index), stream order
        self.cur = 0
        self.slot = None
        self.margin = []        # every decision taken on a raw float comparison
        self.raws = []          # every number before it was rounded for printing

    # -- state a checkpoint carries -------------------------------------------

    def fx(self, x):
        self.raws.append(x)
        return fmt(x)

    def snap(self):
        return copy.deepcopy(
            (self.w, self.v, self.ema, self.applied, self.docs, self.flow, self.cur))

    def unsnap(self, s):
        self.w, self.v, self.ema, self.applied, self.docs, self.flow, self.cur = \
            copy.deepcopy(s)

    # -- the objective, evaluated at the settling step's parameters ------------

    def score(self, d):
        name, n, t, _ = self.docs[d]
        xs = [feat(name, i) for i in range(n)]
        sc = [sum(self.w[k] * x[k] for k in range(FIELDS)) for x in xs]
        top = max(sc)
        ex = [math.exp(s - top) for s in sc]
        z = sum(ex)
        loss = top + math.log(z) - sc[t]
        grad = []
        for k in range(FIELDS):
            grad.append(sum(e * x[k] for e, x in zip(ex, xs)) / z - xs[t][k])
        return loss, grad

    # -- one `step` event ------------------------------------------------------

    def step(self, out):
        c = self.cfg
        want = c["grp"] * c["wrk"] * c["seq"]
        have = (len(self.flow) - self.cur) // c["lim"]
        take = want if want < have else have
        lo, hi = self.cur, self.cur + take * c["lim"]
        self.cur = hi

        ends = []
        for pos in range(lo, hi):
            d, i = self.flow[pos]
            if i == self.docs[d][1] - 1 and self.docs[d][2] >= 0:
                ends.append((pos, d))
        ends.sort()
        done = [d for _, d in ends]
        if not done:
            out.append("nil")
            return

        parts = [self.score(d) for d in done]
        m = len(parts)
        loss = sum(p[0] for p in parts) / m
        grad = [sum(p[1][k] for p in parts) / m for k in range(FIELDS)]
        gn = math.sqrt(sum(g * g for g in grad))
        self.margin.append(("clip", gn - c["clip"]))
        if gn > c["clip"]:
            grad = [g * c["clip"] / gn for g in grad]

        k = self.applied
        if k < c["wu"]:
            lr = c["base"] * (k + 1) / c["wu"]
        else:
            lr = c["base"] * 0.5 ** ((k - c["wu"]) // c["hl"])
        self.v = [c["mu"] * self.v[j] + grad[j] for j in range(FIELDS)]
        self.w = [self.w[j] - lr * self.v[j] for j in range(FIELDS)]
        self.applied = k + 1
        b = min(c["bmax"], (1.0 + self.applied) / (10.0 + self.applied))
        self.ema = [b * self.ema[j] + (1.0 - b) * self.w[j] for j in range(FIELDS)]

        out.append("up %d %s %s %s %s" % (
            self.applied, self.fx(lr), self.fx(loss), self.fx(gn),
            " ".join(self.fx(x) for x in self.w)))
        for j, d in enumerate(done):
            name, n, t, born = self.docs[d]
            self.margin.append(("thr", parts[j][0] - c["thr"]))
            if parts[j][0] > c["thr"] and born < c["cap"]:
                self.push(name, n, t, born + 1)
                out.append("rq " + name)

    def push(self, name, n, t, born):
        d = len(self.docs)
        self.docs.append((name, n, t, born))
        for i in range(n):
            self.flow.append((d, i))

    # -- events ----------------------------------------------------------------

    def ex(self, op, out):
        k = op[0]
        if k == "lim":
            self.cfg["lim"] = int(op[1])
        elif k == "bat":
            self.cfg["grp"], self.cfg["wrk"], self.cfg["seq"] = (int(x) for x in op[1:4])
        elif k == "opt":
            self.cfg["base"] = float(op[1])
            self.cfg["wu"] = int(op[2])
            self.cfg["hl"] = int(op[3])
            self.cfg["mu"] = float(op[4])
            self.cfg["clip"] = float(op[5])
        elif k == "ema":
            self.cfg["bmax"] = float(op[1])
        elif k == "rep":
            self.cfg["thr"] = float(op[1])
            self.cfg["cap"] = int(op[2])
        elif k == "par":
            self.w = [float(x) for x in op[1:5]]
            self.ema = list(self.w)
        elif k == "doc":
            self.push(op[1], int(op[2]), int(op[3]), 0)
            out.append("ad " + op[1])
        elif k == "mdoc":
            self.push(op[1], int(op[2]), -1, 0)
            out.append("ad " + op[1])
        elif k == "resh":
            self.cfg["grp"], self.cfg["wrk"], self.cfg["seq"] = (int(x) for x in op[1:4])
            out.append("rs")
        elif k == "save":
            self.slot = self.snap()
            out.append("ck %d" % self.applied)
        elif k == "load":
            if self.slot is not None:
                self.unsnap(self.slot)
            out.append("ld %d" % self.applied)
        elif k == "emit":
            out.append("em " + " ".join(self.fx(x) for x in self.ema))
        elif k == "step":
            self.step(out)
        else:
            raise ValueError(k)


def expect(lines):
    sim = Sim()
    out = []
    for ln in lines:
        ln = ln.strip()
        if ln:
            sim.ex(tuple(ln.split()), out)
    return out


def margins(lines):
    """Run and report the tightest raw-float decision the trace depended on.

    Every graded line is a rounded number, but two of the decisions behind them
    are taken on unrounded floats: whether the step's gradient is clipped, and
    whether a settled document is requeued. A case whose margin on either is
    smaller than an implementation's own rounding noise would grade an accident,
    so the generator keeps only cases with room to spare.
    """
    sim = Sim()
    out = []
    for ln in lines:
        ln = ln.strip()
        if ln:
            sim.ex(tuple(ln.split()), out)
    tight = min((abs(v) for _, v in sim.margin), default=1.0)
    near = 0.5
    for x in sim.raws:
        frac = abs(x) * 1e6
        near = min(near, abs(frac - math.floor(frac) - 0.5))
    return out, tight, near
