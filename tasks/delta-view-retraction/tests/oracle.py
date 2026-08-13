"""Sealed reference semantics. Shares no code with the engine tree.

This module defines what the view is *supposed* to say, independently of how the engine
computes it. It keeps the full surviving multiset for every group and folds the aggregate
over all of it, with no cap, no accumulator, no cache and no incremental repair. That is
the definition the whole task is measured against: the engine's bounded accumulator is an
optimisation, and an optimisation is only correct when it agrees with this.

It is root-only inside the verifier image and is never importable from the run.

The emit schedule is reproduced here too, because the values the engine logs depend on
when the watermark closed and which cells existed at that moment. That schedule is a
property of the driver the agent may not edit, so reproducing it independently is a check
that the submission did not move it.
"""


def _fold(kind, vals):
    """The aggregate over a group's full surviving multiset. vals is a list of ints."""
    if not vals:
        return 0
    if kind == "sum":
        return sum(vals)
    if kind == "cnt":
        return len(vals)
    if kind == "min":
        return min(vals)
    if kind == "max":
        return max(vals)
    if kind == "top":
        return sum(sorted(set(vals), reverse=True)[:2])
    raise ValueError("unknown kind %r" % kind)


class Truth:
    """Replays a scenario against the full multiset and records what the view must say."""

    def __init__(self, cfg):
        self.spec = cfg["view"]
        self.lag = cfg["lag"]
        self.rows = {}
        self.hi = 0
        self.wm = 0
        self.seq = 0
        self.log = []
        self.trace = []
        self.revised = 0
        self.seen = set()

    def kinds_for(self, src):
        return sorted(k for k, srcs in self.spec.items() if src in srcs)

    def live(self, src, g):
        out = []
        for (rsrc, rk), r in self.rows.items():
            if rsrc == src and r["g"] == g and r["w"] > 0:
                out.append(r["v"])
        return sorted(out)

    def groups(self):
        return sorted(self.seen)

    def feed(self, rec):
        self.seq += 1
        op = rec["op"]
        src = rec["src"]
        k = rec["k"]
        ts = rec["ts"]
        before = self.wm
        if ts > self.hi:
            self.hi = ts
        nw = self.hi - self.lag
        if nw > self.wm:
            self.wm = nw
        after = self.wm

        if ts <= before:
            self.trace.append(["late", self.seq, src, k])
            self.revised += 1

        prior = self.rows.get((src, k))
        if op == "ins":
            self.rows[(src, k)] = {"g": rec.get("g") or "", "v": rec.get("v", 0), "w": 1}
        elif op == "del":
            if prior is not None and prior["w"] > 0:
                self.rows[(src, k)] = {"g": prior["g"], "v": prior["v"], "w": 0}
        elif op == "upd":
            if prior is None or prior["w"] <= 0:
                self.rows[(src, k)] = {"g": rec.get("g") or "", "v": rec.get("v", 0), "w": 1}
            else:
                g = rec.get("g") if rec.get("g") is not None else prior["g"]
                self.rows[(src, k)] = {"g": g, "v": rec.get("v", 0), "w": 1}

        # A cell exists once anything has been routed at it, which is what decides
        # membership of the emit sweep below.
        for (rsrc, rk), r in self.rows.items():
            if rsrc == src:
                self.seen.add(r["g"])

        if after > before:
            self.trace.append(["wm", self.seq, after])
            for kind in sorted(set(self.spec)):
                for g in self.groups():
                    val = _fold(kind, self.live(src, g))
                    self.log.append([self.seq, g, kind, val])
                    self.trace.append(["emit", self.seq, g, kind, val])

    def run(self, ops):
        for rec in ops:
            self.feed(rec)
        return self.view()

    def view(self):
        out = {}
        for g in self.groups():
            for kind in sorted(set(self.spec)):
                srcs = self.spec[kind]
                vals = []
                for s in srcs:
                    vals.extend(self.live(s, g))
                out["%s|%s" % (g, kind)] = _fold(kind, sorted(vals))
        return out
