"""The graded decisions as rows of integer features read off the machine at that moment.

`tools/onelinecheck.py` searches these for the shortest exact rule. The features are raw state
a solver can read at that cycle - counts of ready blocks and of spinners with their line held or
absent, whether a line is cached and where it sits in the fill order, how far a running sum is
from a line. Nothing derived is offered, because the derivation is the task. The rows come from
the sealed model, which defines correct, instrumented from outside so that nothing in it changes;
it is run with sum plans off (mode "spins"), so every line of every sum is a stepped issue and
every row is read at the exact cycle it describes.

Five questions, two of which are expected to be short:

  load_from_cache   does this load answer from a cached copy (short: the rule is local)
  spin_passes       does this attempt get through (short once the value is known)
  hangs_here        does the all-spinning stretch that starts at this cycle never end
  frozen            is every ready block, in such a stretch, a spinner that changes nothing
  store_in_sum      does a store made now end up in the total of a sum running on another
                    multiprocessor whose remaining lines include the stored line

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
        super().__init__(*a, mode="spins")
        self.loads, self.spins, self.skips, self.closed, self.passes = [], [], [], [], set()
        self.now = 0
        self.stores = []          # (t, sm, line, features per running sum) for later labels
        self.reads = {}           # (block, sum serial, line) -> (t, sm, from memory)
        self.serial = [0] * self.G

    def read_line(self, s, cached, line):
        held = line in self.cache[s]
        self.loads.append(({"ca": int(cached), "held": int(held)}, cached and held))
        return super().read_line(s, cached, line)

    def issue(self, b, s, t):
        ins = self.code[self.pc[b]]
        op = ins[0]
        if op in model.SUMS:
            if self.sleft[b] == 0:
                self.serial[b] += 1
                line = self.ea(b, ins[2]) // 4
            else:
                line = self.sline[b]
            memory = op == "sum.cg" or line not in self.cache[s]
            self.reads[(b, self.serial[b], line)] = (t, s, memory)
        if op in ("st", "atom.add"):
            adr = ins[1] if op == "st" else ins[2]
            line = self.ea(b, adr) // 4
            runs = []
            for j in range(self.S):
                if j == s:
                    continue
                c = self.cache[j]
                order = list(c)
                for x in self.slot[j]:
                    if x is None or self.ended[x] is not None or self.sleft[x] == 0:
                        continue
                    ahead = line - self.sline[x]
                    if 0 <= ahead < self.sleft[x]:
                        k = sum(1 for y in self.slot[j] if self.ready(y, t))
                        runs.append(((x, self.serial[x]), {
                            "ahead": ahead, "later_sm": int(j > s),
                            "held": int(line in c),
                            "place": order.index(line) if line in c else -1,
                            "cached": len(c), "cap": self.C, "ready": k,
                        }))
            self.stores.append((t, s, line, runs))
        if op in model.SPINS:
            _, rd, adr, cmp, v = ins
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
        self.closed.append((t, row))
        self.skips.append((row, got))
        return got

    def labelled_stores(self):
        """Each (store, running sum) pair: did the sum read that line from memory after it?"""
        out = []
        for t, s, line, runs in self.stores:
            for key, row in runs:
                read = self.reads.get((key[0], key[1], line))
                if read is None:
                    continue
                rt, rs, memory = read
                after = rt > t or (rt == t and rs > s)
                out.append((row, bool(memory and after)))
        return out


def launches():
    """The small generated families, then more reduce launches and unshaped fuzz launches,
    where a store racing a running sum is common enough to decide anything."""
    import random
    sys.path.insert(0, str(HERE))
    import fuzz_sums
    for fam, _name, lines in gen.programs("decisions", 12):
        if fam not in ("wide", "deep", "stream"):
            yield lines
    for i in range(400):
        yield gen.reduce(random.Random("decisions-reduce:%d" % i))
    for i in range(1500):
        yield fuzz_sums.launch(10 ** 6 + i)


def samples():
    loads, spins, skips, hangs, stores = [], [], [], [], []
    for lines in launches():
        dev, grid, mem, show, code = model.parse(lines)
        m = Probe(dev, grid, mem, code)
        hang = m.run()
        loads += m.loads
        spins += m.spins
        skips += m.skips
        stores += m.labelled_stores()
        prev = None
        for t, row in m.closed:
            start = prev is None or prev != t - 1 or (t - 1) in m.passes
            if start:
                hangs.append((row, t == hang))
            prev = t
    return {"load_from_cache": loads, "spin_passes": spins, "frozen": skips,
            "hangs_here": hangs, "store_in_sum": stores}


if __name__ == "__main__":
    for name, rows in samples().items():
        print("%-16s %5d rows, %d true" % (name, len(rows), sum(1 for _, y in rows if y)))
