"""The sealed model: what the schedule has to be, worked out independently of the engine.

Nothing here shares code with rt/. This is a second scheduler, written to the same published
semantics, and it differs from the engine in the one place that matters: where the engine keeps
effective priority incrementally, patching it as events arrive, this recomputes the whole
priority assignment from scratch after anything moves, by iterating

    worth(t) = max(base(t), max worth(u) for u blocked on a mutex t holds)

to a fixed point over every task. That is the definition the incremental policy is an
optimisation of, so a submitted policy that patches the wrong task, forgets a link of a chain
or leaves a boost standing after the reason for it has gone cannot agree with this.

The other half of the file is the scenario generator. The fixed scenarios are aimed at
particular readings of the rule and their answers live in gt.json; the generated ones are built
at verification time from a seed the run cannot predict, and their answers are computed here,
right then. A submission that recognises a scenario and replays a remembered schedule has
nothing to remember.
"""

import hashlib
import os
import types

NEW = 0
READY = 1
BLOCK = 3
SLEEP = 4
DONE = 5

# The engine functions the run fingerprints. Kept in step with runner.SEALED; build_gt.py
# fails if the two lists ever drift apart.
SEALED = (
    ("rt/core.py", "Core.pick"),
    ("rt/core.py", "Core.set"),
    ("rt/core.py", "Core.ready"),
    ("rt/core.py", "Core.run_one"),
    ("rt/core.py", "Core.top"),
    ("rt/core.py", "Core.expire"),
    ("rt/core.py", "Core.run"),
    ("rt/core.py", "Core.acquire"),
    ("rt/core.py", "Core.report"),
    ("rt/boot.py", "build"),
)


class Model:
    """A scheduler written to the published semantics, with priority solved rather than patched."""

    def __init__(self, cfg, sc):
        self.limit = cfg["limit"]
        self.t = {}
        self.order = []
        for spec in sorted(sc["tasks"], key=lambda x: x["id"]):
            i = spec["id"]
            self.order.append(i)
            self.t[i] = {
                "base": spec["base"],
                "start": spec.get("start", 0),
                "prog": spec["prog"],
                "pc": 0,
                "left": 0,
                "state": NEW,
                "qn": 0,
                "wake": 0,
                "dead": -1,
                "worth": spec["base"],
            }
        self.mx = {}
        for spec in sc["tasks"]:
            for s in spec["prog"]:
                if s[0] in ("lock", "unlock") and s[1] not in self.mx:
                    self.mx[s[1]] = {"h": 0, "q": []}
        self.seq = 0
        self.now = 0
        self.trace = []
        self.prio = []
        self.ev = []

    # -- the priority solution -----------------------------------------------------------

    def solve(self):
        """Iterate worth() to a fixed point over every task."""
        for i in self.order:
            self.t[i]["worth"] = self.t[i]["base"]
        for _ in range(len(self.order) + 2):
            moved = False
            for i in self.order:
                want = self.t[i]["base"]
                for m in self.mx.values():
                    if m["h"] != i:
                        continue
                    for w in m["q"]:
                        if self.t[w]["worth"] > want:
                            want = self.t[w]["worth"]
                if want != self.t[i]["worth"]:
                    self.t[i]["worth"] = want
                    moved = True
            if not moved:
                break

    def note(self, kind, who, what):
        self.ev.append([kind, self.now, who, what])

    def wake_up(self, i):
        self.seq += 1
        self.t[i]["qn"] = self.seq
        self.t[i]["state"] = READY

    # -- the tick ------------------------------------------------------------------------

    def arrivals(self):
        for i in self.order:
            r = self.t[i]
            if r["state"] == NEW and r["start"] <= self.now:
                self.wake_up(i)
            elif r["state"] == SLEEP and r["wake"] <= self.now:
                self.wake_up(i)

    def giveups(self):
        for i in self.order:
            r = self.t[i]
            if r["state"] != BLOCK or r["dead"] < 0 or r["dead"] > self.now:
                continue
            m = self.waiting_on(i)
            if m is None:
                continue
            self.mx[m]["q"].remove(i)
            r["dead"] = -1
            r["pc"] += 1
            r["left"] = 0
            self.wake_up(i)
            self.note("exp", i, m)
            self.solve()

    def waiting_on(self, i):
        for m in sorted(self.mx):
            if i in self.mx[m]["q"]:
                return m
        return None

    def choose(self):
        best = 0
        for i in self.order:
            if self.t[i]["state"] != READY:
                continue
            if best == 0:
                best = i
            elif self.t[i]["worth"] > self.t[best]["worth"]:
                best = i
            elif (self.t[i]["worth"] == self.t[best]["worth"]
                  and self.t[i]["qn"] < self.t[best]["qn"]):
                best = i
        return best

    def take(self, i, m):
        self.mx[m]["h"] = i
        self.note("acq", i, m)
        self.solve()

    def execute(self, i):
        """Run one task until it consumes the tick or gives the processor up."""
        r = self.t[i]
        for _ in range(64):
            if r["pc"] >= len(r["prog"]):
                r["state"] = DONE
                self.note("done", i, 0)
                return False
            s = r["prog"][r["pc"]]
            if s[0] == "run":
                if r["left"] == 0:
                    r["left"] = s[1]
                r["left"] -= 1
                if r["left"] <= 0:
                    r["pc"] += 1
                    r["left"] = 0
                return True
            if s[0] == "lock":
                m = s[1]
                if self.mx[m]["h"] in (0, i):
                    if self.mx[m]["h"] == 0:
                        self.take(i, m)
                    r["pc"] += 1
                    r["left"] = 0
                    continue
                self.mx[m]["q"].append(i)
                r["state"] = BLOCK
                r["dead"] = self.now + s[2] if s[2] >= 0 else -1
                self.note("blk", i, m)
                self.solve()
                return False
            if s[0] == "unlock":
                m = s[1]
                if self.mx[m]["h"] != i:
                    r["pc"] += 1
                    r["left"] = 0
                    continue
                self.mx[m]["h"] = 0
                r["pc"] += 1
                r["left"] = 0
                self.note("rel", i, m)
                self.solve()
                q = self.mx[m]["q"]
                if q:
                    nxt = q.pop(0)
                    self.t[nxt]["dead"] = -1
                    self.take(nxt, m)
                    self.t[nxt]["pc"] += 1
                    self.t[nxt]["left"] = 0
                    self.wake_up(nxt)
                continue
            if s[0] == "sleep":
                r["pc"] += 1
                r["left"] = 0
                r["state"] = SLEEP
                r["wake"] = self.now + s[1]
                self.note("slp", i, s[1])
                return False
            r["pc"] += 1
            r["left"] = 0
        return False

    def busy(self):
        return any(self.t[i]["state"] != DONE for i in self.order)

    def run(self):
        self.solve()
        while self.now < self.limit and self.busy():
            self.arrivals()
            self.giveups()
            ran = 0
            for _ in range(32):
                i = self.choose()
                if i == 0:
                    break
                if self.execute(i):
                    ran = i
                    break
            self.trace.append([self.now, ran])
            self.prio.append([self.now] + [self.t[i]["worth"] for i in self.order])
            self.now += 1
        return self.now

    def report(self):
        return {
            "trace": [list(x) for x in self.trace],
            "prio": [list(x) for x in self.prio],
            "ev": [list(x) for x in self.ev],
            "ids": list(self.order),
            "ticks": self.now,
            "done": [[i, self.finished(i)] for i in self.order],
        }

    def finished(self, i):
        for e in self.ev:
            if e[0] == "done" and e[2] == i:
                return e[1]
        return -1


def expect(cfg, sc):
    m = Model(cfg, sc)
    m.run()
    return m.report()


# -- attestation --------------------------------------------------------------------------

def fingerprint(code):
    h = hashlib.sha256()
    h.update(code.co_code)
    h.update(repr(code.co_names).encode("utf-8"))
    h.update(repr(code.co_varnames).encode("utf-8"))
    for k in code.co_consts:
        if isinstance(k, types.CodeType):
            h.update(fingerprint(k).encode("utf-8"))
        else:
            h.update(repr(k).encode("utf-8"))
    return h.hexdigest()


def walk(code, parts):
    if not parts:
        return code
    for k in code.co_consts:
        if isinstance(k, types.CodeType) and k.co_name == parts[0]:
            return walk(k, parts[1:])
    return None


def expected_fingerprints(root):
    """Compile the pristine sources and derive what the run's fingerprints have to be.

    Nothing is executed: the sources are compiled and the code objects walked by name.
    """
    out = {}
    for rel, qual in SEALED:
        path = os.path.join(root, rel)
        if not os.path.isfile(path):
            continue
        with open(path) as fh:
            top = compile(fh.read(), rel, "exec")
        code = walk(top, qual.split("."))
        if code is not None:
            out["%s:%s" % (rel, qual)] = fingerprint(code)
    return out
