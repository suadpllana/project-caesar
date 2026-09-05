"""Does the generated set exercise the conditions the task is built on, and how many
scripts does each wrong reading move?

The first half instruments the sealed model: for each generated script it counts the
deferred situations - a return resolved through a screen that had gone, a return or a
held request whose widget was disturbed and restored under the push, a held request
resolved, a key started from a lost place, a place chained through a dropped container.
The second half runs every wrong reading against the reference and reports the share of
scripts whose trail changes. A reading under a tenth is a lottery ticket, not a decision.

Usage: coverage.py [n]
"""

import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(TASK, "tests"))

import gen  # noqa: E402
import harness  # noqa: E402
import oracle  # noqa: E402
import readings  # noqa: E402


class Probe(oracle.Sim):
    def __init__(self):
        oracle.Sim.__init__(self)
        self.hits = {}
        self.touched = {}      # wid -> disturbed while a record pointed at it

    def hit(self, k):
        self.hits[k] = self.hits.get(k, 0) + 1

    def fix(self, t):
        if t is not None and self.is_screen(t[1]) and not self.live(t[1]):
            self.hit("chain-through-dead-screen")
        if t is not None and t[0] == "p" and not self.is_screen(t[1]) and not self.live(t[1]):
            self.hit("chain-through-dropped-container")
        return oracle.Sim.fix(self, t)

    def pop(self, s):
        was_top = self.stack and self.stack[-1] == s
        if not was_top and s in self.stack:
            self.hit("pop-out-of-order")
        if was_top and len(self.stack) > 1:
            t = self.stack[-2]
            if t in self.held:
                self.hit("held-resolved")
                w = self.held[t]
                if self.touched.get(w) == "restored":
                    self.hit("held-restored-before-return")
                elif not self.can_at(w):
                    self.hit("held-unreachable-at-return")
            r = self.ret.get(s)
            if r is not None and r[0] == "w":
                if self.touched.get(r[1]) == "restored":
                    self.hit("return-restored-before-pop")
                elif self.live(r[1]) and not self.can_at(r[1]):
                    self.hit("return-unreachable-at-pop")
                elif not self.live(r[1]):
                    self.hit("return-target-gone")
        oracle.Sim.pop(self, s)

    def can_at(self, w):
        return self.live(w) and "foc" in self.fl[w] and \
            all(not (self.fl[c] & oracle.BLOCK) for c in self.chain(w))

    def key(self, fwd):
        if self.focus is None and self.orig is not None and self.stops():
            self.hit("key-from-lost-place")
        oracle.Sim.key(self, fwd)

    def mutate(self, toks):
        k = toks[0]
        watched = set(w for _, w in self.held.items()) | \
            set(r[1] for r in self.ret.values() if r is not None and r[0] == "w")
        if k in ("hide", "off", "shut", "drop") and toks[1] in watched:
            for w in watched:
                if w == toks[1] or (toks[1] in self.chain(w) if w in self.par else False):
                    self.touched[w] = "disturbed"
        if k in ("show", "on", "open"):
            for w in list(self.touched):
                if self.touched[w] == "disturbed" and w in self.par and \
                        (w == toks[1] or toks[1] in self.chain(w)):
                    self.touched[w] = "restored"
        oracle.Sim.mutate(self, toks)


def probe(text):
    sim = Probe()
    for raw in text.split("\n"):
        toks = raw.split()
        if not toks:
            continue
        if toks[0] == "screen":
            sim.screen(toks[1])
        elif toks[0] == "w":
            fl, grp = oracle.split_flags(toks[3:])
            sim.widget(toks[1], toks[2], fl, grp)
        else:
            sim.event(toks)
    return sim.hits


def main(argv):
    n = int(argv[1]) if len(argv) > 1 else 300
    items = gen.batch("coverage", n)
    totals = {}
    for _, text in items:
        for k in probe(text):
            totals[k] = totals.get(k, 0) + 1
    print("scripts in which each situation occurs (of %d):" % n)
    for k in sorted(totals, key=lambda x: -totals[x]):
        print("   %-36s %4d  %5.1f%%" % (k, totals[k], 100.0 * totals[k] / n))
    print("\nscripts each wrong reading moves:")
    ref = [harness.run_inproc(readings.REFERENCE, t) for _, t in items]
    low = 0
    for name in sorted(readings.READINGS):
        d = tempfile.mkdtemp(prefix="reading-")
        for fn in harness.POL:
            shutil.copyfile(os.path.join(readings.REFERENCE, fn), os.path.join(d, fn))
        for fn, src in readings.READINGS[name].items():
            with open(os.path.join(d, fn), "w") as fh:
                fh.write(src)
        moved = 0
        for (nm, text), want in zip(items, ref):
            try:
                got = harness.run_inproc(d, text)
            except Exception:
                got = ("error",)
            if got != want:
                moved += 1
        share = 100.0 * moved / n
        flag = "" if share >= 10 else "   LOTTERY"
        low += 1 if share < 10 else 0
        print("   %-32s %5.1f%%%s" % (name, share, flag))
    return 1 if low else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
