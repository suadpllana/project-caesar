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

The second half of the file is the evidence side. A report is a claim; the work journal
view/core.py records is the evidence for it, and Bag/replay/audit below are what turn that
evidence back into the claim. Bag is a second, independently written implementation of the
bounded accumulator in store/agg.py: replay folds the recorded work through it and must
land on the values the submission published, and audit checks every record against what
the scenario makes possible - a rebuild must fold exactly the group the row store held at
that moment, an incremental fold must correspond to an edit that delta actually produced,
and neither may be charged to a cell the delta never touched. Counters are not trusted at
all: they are required to equal the journal, and the journal has to survive both passes.
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
        self.edits_at = {}
        self.src_at = {}
        self.live_at = {}

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

        # The edits a delta produces, derived here rather than read from the engine: the
        # prior row leaves its group with weight -1, the row that lands joins its group
        # with weight +1, and a delta that changes nothing produces neither. audit() uses
        # this to decide which folds a submission was entitled to charge for.
        prior = self.rows.get((src, k))
        edits = []
        if prior is not None and prior["w"] > 0:
            edits.append([prior["g"], prior["v"], -1])
        landed = None
        if op == "ins":
            landed = {"g": rec.get("g") or "", "v": rec.get("v", 0), "w": 1}
        elif op == "del":
            if prior is None or prior["w"] <= 0:
                edits = []
            else:
                landed = {"g": prior["g"], "v": prior["v"], "w": 0}
        elif op == "upd":
            if prior is None or prior["w"] <= 0:
                landed = {"g": rec.get("g") or "", "v": rec.get("v", 0), "w": 1}
            else:
                g = rec.get("g") if rec.get("g") is not None else prior["g"]
                landed = {"g": g, "v": rec.get("v", 0), "w": 1}
        else:
            edits = []
        if landed is not None:
            self.rows[(src, k)] = landed
            if landed["w"] > 0:
                edits.append([landed["g"], landed["v"], 1])

        self.edits_at[self.seq] = edits
        self.src_at[self.seq] = src
        for e in edits:
            self.live_at[(self.seq, e[0])] = self.live(src, e[0])

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

    def kinds_for(self, src):
        return set(k for k, srcs in self.spec.items() if src in srcs)


# ---------------------------------------------------------------------------
# The evidence side.
#
# CAP is the bound store/agg.py holds its candidates under. It is restated here rather
# than imported, because the point of this module is to be a second opinion: if the two
# ever drift apart, build_gt.py fails before a ground truth is written.

CAP = 3


class Bag:
    """A second implementation of the bounded accumulator, written independently.

    Same semantics as store/agg.py and none of its code: a running total for the
    invertible kinds, and for the order-sensitive ones a candidate map that keeps the CAP
    best distinct values and silently forgets the rest.
    """

    __slots__ = ("kind", "tot", "mult", "cand")

    def __init__(self, kind):
        self.kind = kind
        self.tot = 0
        self.mult = 0
        self.cand = {}

    def _best(self, vals):
        if self.kind == "min":
            return sorted(vals)
        return sorted(vals, reverse=True)

    def fold(self, v, w):
        if self.kind == "sum":
            self.tot += v * w
            self.mult += w
            return
        if self.kind == "cnt":
            self.mult += w
            self.tot = self.mult
            return
        self.mult += w
        if v in self.cand:
            left = self.cand[v] + w
            if left > 0:
                self.cand[v] = left
            else:
                del self.cand[v]
        elif w > 0:
            self.cand[v] = w
            if len(self.cand) > CAP:
                for gone in self._best(list(self.cand))[CAP:]:
                    del self.cand[gone]
        order = self._best(list(self.cand))
        if not order:
            self.tot = 0
        elif self.kind == "top":
            self.tot = sum(order[:2])
        else:
            self.tot = order[0]

    def value(self):
        return self.tot


def shape(journal):
    """Reject anything that is not a well formed journal, before it is interpreted."""
    if not isinstance(journal, list):
        return "the work journal is not a list"
    for i, e in enumerate(journal):
        if not isinstance(e, list) or not e or e[0] not in ("f", "s", "e"):
            return "record %d is not a journal entry: %r" % (i, e)
        want = {"f": 6, "s": 4, "e": 5}[e[0]]
        if len(e) != want:
            return "record %d has %d fields, expected %d: %r" % (i, len(e), want, e)
        if not isinstance(e[1], int) or isinstance(e[1], bool):
            return "record %d carries no delta number: %r" % (i, e)
        if not isinstance(e[2], str) or not isinstance(e[3], str):
            return "record %d names no cell: %r" % (i, e)
        for j in range(4, want):
            if not isinstance(e[j], int) or isinstance(e[j], bool):
                return "record %d field %d is not an integer: %r" % (i, j, e[j])
    return None


def replay(journal):
    """Fold the recorded work back through the sealed accumulator.

    Returns (view, emitted, problem). The view is what the recorded work actually
    produces, which is the only thing a submission is allowed to have published.
    """
    cells = {}
    emitted = []
    for i, e in enumerate(journal):
        key = (e[2], e[3])
        if e[0] == "s":
            cells[key] = Bag(e[3])
        elif e[0] == "f":
            if key not in cells:
                cells[key] = Bag(e[3])
            cells[key].fold(e[4], e[5])
        else:
            held = cells.get(key)
            was = 0 if held is None else held.value()
            if was != e[4]:
                return None, None, (
                    "record %d publishes %s|%s as %d, but the work recorded up to that "
                    "point makes it %d" % (i, e[2], e[3], e[4], was))
            emitted.append([e[1], e[2], e[3], e[4]])
    view = {}
    for (g, kind), held in cells.items():
        view["%s|%s" % (g, kind)] = held.value()
    return view, emitted, None


def audit(journal, ops, cfg):
    """Check every record against what the scenario actually made possible.

    A rebuild has to fold exactly the group the row store held at that moment. An
    incremental fold has to correspond to an edit that delta really produced, and it may
    be charged once. Neither may be charged to a group the delta never touched, or to an
    aggregate the source does not feed. This is what stops a journal from being written
    rather than earned.
    """
    t = Truth(cfg)
    t.run(ops)
    n = len(ops)
    owed = {}
    for seq, edits in t.edits_at.items():
        for kind in t.kinds_for(t.src_at[seq]):
            for e in edits:
                owed.setdefault((seq, e[0], kind), []).append([e[1], e[2]])

    last = 0
    i = 0
    while i < len(journal):
        e = journal[i]
        tag, seq, g, kind = e[0], e[1], e[2], e[3]
        if tag == "e":
            i += 1
            continue
        if seq < 1 or seq > n:
            return "record %d is charged to delta %d, which is not in the scenario" % (i, seq)
        if seq < last:
            return "record %d is charged to delta %d after work for delta %d" % (i, seq, last)
        last = seq
        src = t.src_at[seq]
        if kind not in t.kinds_for(src):
            return "record %d charges work to %s, which %s does not feed" % (i, kind, src)
        touched = set(x[0] for x in t.edits_at[seq])
        if g not in touched:
            return ("record %d charges work to group %s, which delta %d does not touch"
                    % (i, g, seq))
        if tag == "s":
            live = sorted(t.live_at.get((seq, g), []))
            got = []
            j = i + 1
            while j < len(journal) and len(got) < len(live):
                nxt = journal[j]
                if nxt[0] != "f" or nxt[1] != seq or nxt[2] != g or nxt[3] != kind:
                    break
                if nxt[5] != 1:
                    return ("record %d rebuilds %s|%s with a weight of %d; a group read "
                            "from the row store holds live rows only"
                            % (j, g, kind, nxt[5]))
                got.append(nxt[4])
                j += 1
            if sorted(got) != live:
                return ("record %d rereads %s|%s from the row store but folds %s, where "
                        "the group holds %s at delta %d"
                        % (i, g, kind, sorted(got), live, seq))
            i = j
            continue
        left = owed.get((seq, g, kind))
        pair = [e[4], e[5]]
        if not left or pair not in left:
            return ("record %d folds %r into %s|%s, which is not an edit delta %d "
                    "produced for that cell" % (i, pair, g, kind, seq))
        left.remove(pair)
        i += 1
    return None
