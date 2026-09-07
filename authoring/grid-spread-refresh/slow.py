"""A third reading of the contract, written to be obviously right rather than fast.

Neither the reference nor the sealed model settles the sheet from scratch, and an earlier
run of this kit found a rule both of them had got wrong in the same way. So this one drops
incremental machinery entirely and encodes the rule as it is stated:

  after an edit, the sheet ends up in the state a full evaluation would produce, and the
  cells that were recomputed are exactly the formula cells whose previous read record
  disagrees with that final state.

The final state is reached by re-evaluating every formula cell, in address order, until a
whole pass changes nothing. The recomputed set then falls out in one comparison, with no
ordering question to get wrong - which is the point of having it.

Only the frozen expression evaluator is shared with the runtime; the record keeping, the
layout and the settling here are written from the stated rules.

    python3 authoring/grid-spread-refresh/slow.py [count]
"""

import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "tasks", "grid-spread-refresh", "tests"))

import tree  # noqa: E402

APP = tree.ref()
sys.path.insert(0, APP)

import gen  # noqa: E402
import oracle  # noqa: E402
from sheet import adr, expr, store  # noqa: E402

BLK = store.BLK


class Peek:
    def __init__(self, dv, ow):
        self.dv = dv
        self.ow = ow
        self.rd = []

    def val(self, ad):
        v = self.dv.get(ad)
        self.rd.append(("v", ad, v))
        return v

    def own(self, ad):
        b = ad in self.ow
        self.rd.append(("o", ad, b))
        return b


class Sheet:
    def __init__(self, nr):
        self.nr = nr
        self.ow = {}
        self.dv = {}
        self.rec = {}

    def formulas(self):
        return sorted(a for a, e in self.ow.items() if e[0] == "f")

    def evaluate(self, ad, dv):
        """One evaluation against the display map `dv`; returns (reads, writes)."""
        pk = Peek(dv, self.ow)
        kind, vals = expr.run(self.ow[ad][1], pk)
        writes = {}
        if kind != "v":
            return pk.rd, {ad: vals}, []
        want = [(ad[0] + i, ad[1]) for i in range(1, len(vals))]
        fits = True
        for t in want:
            if t[0] > self.nr:
                fits = False
            elif pk.own(t):
                fits = False
        seen = set(t for k, t, _ in pk.rd if k == "v")
        if not fits or any(t in seen for t in want):
            return pk.rd, {ad: BLK}, []
        writes[ad] = vals[0] if vals else None
        for i, t in enumerate(want):
            writes[t] = vals[i + 1]
        return pk.rd, writes, want

    def settle(self):
        """Re-evaluate everything until a whole pass leaves the display map alone."""
        for _ in range(200):
            dv = {}
            for ad, e in self.ow.items():
                if e[0] == "n":
                    dv[ad] = e[1]
            reads = {}
            for ad in self.formulas():
                rd, writes, _ = self.evaluate(ad, self.dv)
                reads[ad] = rd
                for t, v in writes.items():
                    if t in self.ow and t != ad:
                        continue
                    if v is not None:
                        dv[t] = v
            if dv == self.dv:
                return reads
            self.dv = dv
        raise RuntimeError("did not settle")

    def agrees(self, ad):
        rd = self.rec.get(ad)
        if rd is None:
            return False
        for k, t, was in rd:
            now = (t in self.ow) if k == "o" else self.dv.get(t)
            if now != was:
                return False
        return True

    def apply(self, line):
        before = dict(self.dv)
        t = line.split(None, 2)
        ad = adr.pa(t[1])
        if t[0] == "clr":
            if self.ow.pop(ad, None) is None:
                return "-", "-"
        else:
            body = t[2].strip()
            if body.startswith("="):
                self.ow[ad] = ("f", expr.parse(body[1:]))
            else:
                self.ow[ad] = ("n", int(body))
        self.rec.pop(ad, None)
        stale = [a for a in self.formulas() if not self.agrees(a)]
        reads = self.settle()
        hit = sorted(a for a in self.formulas()
                     if a in stale or not self.agrees(a))
        for a in hit:
            self.rec[a] = reads[a]
        for a in list(self.rec):
            if a not in self.ow or self.ow[a][0] != "f":
                del self.rec[a]
        moves = []
        for a in sorted(set(before) | set(self.dv)):
            if before.get(a) != self.dv.get(a):
                moves.append("%s=%s" % (adr.fa(a), store.sho(self.dv.get(a))))
        return (" ".join(adr.fa(a) for a in hit) or "-",
                " ".join(moves) or "-")


def solve(text):
    sh = None
    live = False
    k = 0
    out = []
    for raw in text.split("\n"):
        s = raw.strip()
        if not s:
            continue
        t = s.split(None, 2)
        if t[0] == "size":
            sh = Sheet(int(t[1]))
            continue
        if t[0] == "go":
            live = True
            continue
        seen, moves = sh.apply(s)
        if not live:
            continue
        k += 1
        out.append("rc %d %s" % (k, seen))
        out.append("dv %d %s" % (k, moves))
    return out


def main(argv):
    n = int(argv[1]) if len(argv) > 1 else 12
    bad = 0
    t0 = time.time()
    scripts = gen.batch("slow-v1", n)
    for name, text in scripts:
        want = oracle.solve(text)
        got = solve(text)
        if got == want:
            continue
        bad += 1
        for i in range(max(len(got), len(want))):
            a = got[i] if i < len(got) else "<missing>"
            b = want[i] if i < len(want) else "<missing>"
            if a != b:
                print("%s line %d\n   slow  %s\n   model %s" % (name, i, a, b))
                break
        if bad > 5:
            break
    print("%d scripts, %d disagreements, %.1fs" % (len(scripts), bad, time.time() - t0))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
