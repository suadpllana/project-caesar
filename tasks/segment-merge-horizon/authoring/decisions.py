"""The graded decisions the reference makes, as rows tools/onelinecheck.py can search.

The question that gate asks is how short the answer is: if every decision the verifier
grades can be reproduced by a one or two term comparison between fields the environment
already hands over, then the answer is something a frontier model writes cold, before it
has run anything, and the easiness probe will solve it three times out of three.

Three decisions are recorded here, each described by what a plan can see at the moment it
has to decide, without paying for a record:

  read-depth   how many records the reference pulls for one key of one job. The features
               are the ones a plan can read for free - how many read points the job has,
               how many records the key holds across the participating segments, and how
               many of those segments hold it at all.
  ask-outside  whether the reference spends a point read on this key.
  drop-lowest  whether the lowest outcome ends up written or dropped.

The second and third are deliberately included even though they are the parts a careful
solver gets right early. If they came back short and read-depth did not, that is the shape
this task is built on and the gate says so.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

TASK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TASK / "tests"))

import scen  # noqa: E402

PUT = 0
DEL = 1
ADD = 2


def cfg_for(sc):
    cfg = json.loads((TASK / "tests" / "store.json").read_text())
    cfg.update(sc.get("cfg") or {})
    return cfg


class Store:
    """Enough of the engine to replay a stream and hand out each job's per key input."""

    def __init__(self, tier):
        self.tier = tier
        self.segs = []
        self.mem = []
        self.pins = []
        self.seq = 0
        self.dirty = False

    def pts(self):
        return sorted(set(list(self.pins) + [self.seq]))

    def seal(self):
        if self.dirty:
            self.segs.insert(0, sorted(self.mem, key=lambda r: (r[0], -r[1])))
            self.mem = []
            self.dirty = False

    def width(self):
        n = len(self.segs)
        if n < 2:
            return 0
        w = self.tier if self.tier <= n else n
        return w if w >= 2 else 0

    def step(self, o):
        t = o["op"]
        if t in ("put", "del", "add"):
            self.seq += 1
            kind = PUT if t == "put" else (DEL if t == "del" else ADD)
            v = o["v"] if t == "put" else (o["d"] if t == "add" else 0)
            self.mem.append((o["k"], self.seq, kind, v))
            self.dirty = True
        elif t == "flush":
            self.seal()
        elif t == "pin":
            self.pins.append(self.seq)
        elif t == "unpin":
            i = o["i"]
            if 0 <= i < len(self.pins):
                self.pins.pop(i)
        elif t == "merge":
            self.seal()
            return True
        return False


def resolve(rs):
    acc = 0
    n = 0
    for s, t, v in rs:
        if t == ADD:
            acc += v
        elif t == PUT:
            return acc + v
        else:
            return acc if n else None
        n += 1
    return acc if n else None


def pull(rows, pts):
    """The reference's stop rule, as a count."""
    pend = list(pts)
    term = False
    taken = 0
    for k, s, t, v in rows:
        taken += 1
        fresh = [a for a in pend if a >= s]
        if fresh:
            for a in fresh:
                pend.remove(a)
            term = False
        if t != ADD:
            term = True
        if not pend and term:
            break
    return taken


def outcomes(rows, pts, depth):
    seen = rows[:depth]
    outs = []
    last = -1
    for a in sorted(pts):
        i = 0
        while i < len(seen) and seen[i][1] > a:
            i += 1
        if i >= len(seen) or i == last:
            continue
        last = i
        acc = 0
        n = 0
        kind = None
        val = 0
        for x in seen[i:]:
            if x[2] == ADD:
                acc += x[3]
                n += 1
            elif x[2] == PUT:
                kind, val = "v", acc + x[3]
                break
            else:
                kind, val = ("v", acc) if n else ("z", 0)
                break
        if kind is None:
            kind, val = "o", acc
        outs.append((seen[i][1], kind, val))
    return outs


def samples():
    depth = []
    ask = []
    drop = []
    for sc in scen.SCENARIOS:
        cfg = cfg_for(sc)
        st = Store(cfg["tier"])
        for o in sc["ops"]:
            if not st.step(o):
                continue
            w = st.width()
            if not w:
                continue
            part = st.segs[:w]
            rest = st.segs[w:]
            pts = st.pts()
            cover = {}
            for rs in part:
                for r in rs:
                    cover.setdefault(r[0], []).append(r)
            out = []
            for k in sorted(cover):
                rows = sorted(cover[k], key=lambda r: -r[1])
                nsegs = sum(1 for rs in part if any(r[0] == k for r in rs))
                free = {"points": len(pts), "records": len(rows), "segments": nsegs,
                        "newest": 1 if rows[0][2] == PUT else 0,
                        "below": sum(1 for a in pts if a < rows[0][1])}
                d = pull(rows, pts)
                depth.append((free, d))
                outs = outcomes(rows, pts, d)
                if not outs:
                    continue
                s, kind, val = outs[0]
                base = resolve([(r[1], r[2], r[3]) for r in
                                sorted([r for rs in rest for r in rs if r[0] == k],
                                       key=lambda r: -r[1])])
                asked = not (kind == "o" and val)
                shown = {"points": len(pts), "records": len(rows), "outcomes": len(outs),
                         "lowest": {"v": 0, "z": 1, "o": 2}[kind],
                         "total": val if kind == "o" else 0}
                ask.append((shown, asked))
                if asked:
                    if kind == "z":
                        gone = base is None
                    elif kind == "o":
                        gone = base is not None and val == 0
                    else:
                        gone = base == val
                else:
                    gone = False
                seen = dict(shown)
                seen["outside"] = 1 if base is not None else 0
                seen["match"] = 1 if (base is not None and base == val) else 0
                drop.append((seen, gone))
                for r in rows[:0]:
                    out.append(r)
            # the job's output is not needed to describe its decisions
            st.segs = [[]] + st.segs[w:]
    return {"read-depth": depth, "ask-outside": ask, "drop-lowest": drop}
