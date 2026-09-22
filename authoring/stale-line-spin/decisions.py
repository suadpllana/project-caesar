"""The graded decisions as rows of integer features read off the machine at that moment.

`tools/onelinecheck.py` searches these for the shortest exact rule. The features are raw counts a
solver can read off the state at that cycle - how many ready blocks there are, how many of them
spin through the cache with their line held, how many bypass with their line absent, how many
would get through right now, how many blocks are busy, how many were never placed. Nothing
derived is offered, because the derivation is the task. The rows come from the sealed model,
which defines correct, instrumented from outside so that nothing in it changes.

Four questions, two of which are expected to be short:

  load_from_cache   does this load answer from a cached copy (short: the rule is local)
  spin_passes       does this attempt get through (short once the value is known)
  frozen            may the clock jump from this cycle to the next wake
  hangs_here        does the all-spinning stretch that starts at this cycle never end

    python3 authoring/stale-line-spin/decisions.py
"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
TASK = HERE.parents[1] / "tasks" / "stale-line-spin"
sys.path.insert(0, str(TASK / "tests" / "seal"))
sys.path.insert(0, str(TASK / "tests"))

import gen  # noqa: E402
import model  # noqa: E402


def _counts(m, t):
    """Raw counts over the ready blocks at cycle t."""
    c = dict(ready=0, nonspin=0, ca=0, ca_held=0, cg=0, cg_absent=0, pass_now=0,
             busy=len(m.heap), left=m.G - m.nxt)
    for s in range(m.S):
        for b in m.slot[s]:
            if not m.ready(b, t):
                continue
            c["ready"] += 1
            if not m.is_spin(m.pc[b]):
                c["nonspin"] += 1
                continue
            op, rd, adr, cmp, v = m.code[m.pc[b]]
            a = m.ea(b, adr)
            line, w = a // 4, a % 4
            held = line in m.cache[s]
            if op == "spin.ca":
                c["ca"] += 1
                c["ca_held"] += held
                got = m.cache[s][line][w] if held else m.gm.get(a, 0)
            else:
                c["cg"] += 1
                c["cg_absent"] += not held
                got = m.gm.get(a, 0)
            c["pass_now"] += model.CMP[cmp](got, m.val(b, v))
    return c


class Probe(model.Machine):
    def __init__(self, *a):
        super().__init__(*a)
        self.loads, self.spins, self.skips, self.closed, self.passes = [], [], [], [], set()

    def load(self, s, op, a):
        held = (a // 4) in self.cache[s]
        ca = op in ("ld.ca", "spin.ca")
        self.loads.append(({"ca": int(ca), "held": int(held)}, ca and held))
        return super().load(s, op, a)

    def issue(self, b, s, t):
        ins = self.code[self.pc[b]]
        if ins[0] in model.SPINS:
            op, rd, adr, cmp, v = ins
            a = self.ea(b, adr)
            line, w = a // 4, a % 4
            held = line in self.cache[s]
            want = self.val(b, v)
            got = self.cache[s][line][w] if (op == "spin.ca" and held) else self.gm.get(a, 0)
            row = {"got": got, "want": want, "ca": int(op == "spin.ca"), "held": int(held)}
            what = super().issue(b, s, t)
            self.spins.append((row, what == "success"))
            if what == "success":
                self.passes.add(t)
            return what
        return super().issue(b, s, t)

    def frozen(self, t):
        got = super().frozen(t)
        row = _counts(self, t)
        if self.at_spin == self.live and not self.heap:
            self.closed.append((t, row))
        else:
            self.skips.append((row, got))
        return got


def samples():
    loads, spins, skips, hangs = [], [], [], []
    for fam, _name, lines in gen.programs("decisions", 12):
        if fam in ("wide", "deep"):
            continue
        dev, grid, mem, show, code = model.parse(lines)
        m = Probe(dev, grid, mem, code)
        hang = m.run()
        loads += m.loads
        spins += m.spins
        skips += m.skips
        prev = None
        for t, row in m.closed:
            start = prev is None or prev != t - 1 or (t - 1) in m.passes
            if start:
                hangs.append((row, t == hang))
            prev = t
    return {"load_from_cache": loads, "spin_passes": spins, "frozen": skips,
            "hangs_here": hangs}


if __name__ == "__main__":
    for name, rows in samples().items():
        print("%-16s %5d rows, %d true" % (name, len(rows), sum(1 for _, y in rows if y)))
