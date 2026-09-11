"""The graded decisions as rows of features the agent can actually read.

`tools/onelinecheck.py` searches for the shortest exact rule over these. The features offered
are the raw ones the shipped tree exposes at that moment - what a rank has left to spend, how
long the parameter is, where its shard boundaries cut it, and the one pending number a
per-parameter reading carries. Nothing per-slot is offered, and nothing already divided,
because the per-slot state and the division are the derivation and the derivation is the task.

The three quantities:

  spend-slots   how many of a parameter's slots a rank applies on one visit
  map-place     where a parameter sits in the map after it is laid again
  load-owner    which parameter a restored flat position belongs to

None of them should have a short rule. `spend-slots` must not, because the answer depends on
what is pending slot by slot and the tree records one number per parameter; `load-owner` must
not, because the answer is about a layout that has since moved.

    python3 tools/onelinecheck.py shard-spend-carry
"""
import pathlib
import shutil
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
TASK = HERE.parent.parent / "tasks" / "shard-spend-carry"
PARTS = ("cell.py", "lay.py", "cut.py", "walk.py", "tick.py", "keep.py")
SKIP = {"wide", "deep"}

ROWS = {"spend-slots": [], "map-place": [], "load-owner": []}


def tree(over):
    room = pathlib.Path(tempfile.mkdtemp(prefix="ssc-dec-"))
    here = room / "app"
    shutil.copytree(TASK / "environment" / "app_src", here)
    for part in PARTS:
        shutil.copy(over / part, here / "opt" / part)
    return here


def _slots(c):
    """Per-slot pending, expanded - authoring only, and only for small parameters."""
    out = []
    for cnt, _v, _m, g in c.rows:
        out.extend([g] * cnt)
    return out


def hook(cell, lay, keep):
    raw_spend = cell.Cell.spend

    def spend(self, lo, hi, left):
        before = _slots(self)
        got = raw_spend(self, lo, hi, left)
        after = _slots(self)
        done = sum(1 for i in range(lo, hi) if before[i] != 0 and after[i] == 0)
        gs = [r[3] for r in self.rows] or [0]
        ROWS["spend-slots"].append((
            {"left": left, "n": self.n, "lo": lo, "hi": hi, "span": hi - lo,
             "g0": before[lo] if lo < len(before) else 0,
             "absg0": abs(before[lo]) if lo < len(before) else 0,
             "gmax": max(gs), "runs": len(self.rows)},
            done))
        return got

    cell.Cell.spend = spend

    raw_fix = lay.fix

    def fix(r):
        was = {name: i for i, name in enumerate(r.map)}
        live = [n for n in r.order if r.par[n].live]
        raw_fix(r)
        for i, name in enumerate(r.map):
            c = r.par[name]
            ROWS["map-place"].append((
                {"decl": r.order.index(name), "prev": was.get(name, -1),
                 "was": int(name in was), "since": c.since, "nlive": len(live),
                 "nmap": len(r.map), "n": c.n}, i))

    lay.fix = fix

    raw_load = keep.load

    def load(r, tag):
        plan = r.ck[tag][0]
        now = {name: i for i, name in enumerate(r.map)}
        for i, (name, n) in enumerate(plan):
            ROWS["load-owner"].append((
                {"now": now.get(name, -1), "n": n, "nmap": len(r.map),
                 "nsaved": len(plan), "live": int(r.par[name].live)}, i))
        return raw_load(r, tag)

    keep.load = load


def samples():
    here = tree(TASK / "solution")
    sys.path.insert(0, str(here))
    sys.path.insert(0, str(TASK / "tests"))
    import gen
    import ops
    from opt import cell, keep, lay, reg

    hook(cell, lay, keep)
    for fam, _name, lines in gen.programs("decisions", 25):
        if fam in SKIP:
            continue
        r = reg.Reg()
        for line in lines:
            t = tuple(line.split())
            if t:
                ops.ex(r, t)
    shutil.rmtree(here.parent, ignore_errors=True)
    return ROWS
