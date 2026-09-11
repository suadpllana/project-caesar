#!/usr/bin/env python3
"""Build the forgery: an engine that carries the frozen answers to the enumerated programs and
hands them back, keyed by the ops it has seen.

It exists to prove the nonce population is doing its job, so it has to reach the nonce
population. Built on the shipped engine it did not: the shipped engine cannot finish the two
scale families inside the wall clock, the worker was killed, and the run scored 0 for the
clock rather than for the answers. It is therefore built on one wrong reading of the
reference - fast enough to finish, wrong enough that the generated programs separate it - with
the frozen answers laid over the enumerated ones. This script asserts that it still reproduces
every frozen answer, because a forgery that quietly stopped doing so proves nothing.
"""
import hashlib
import json
import pathlib
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
TASK = ROOT / "tasks" / "shard-spend-carry"
SRC = pathlib.Path(__file__).resolve().parent / "readings" / "spend-strict"
OUT = pathlib.Path(__file__).resolve().parent / "handonly"
PARTS = ("cell.py", "lay.py", "cut.py", "walk.py", "tick.py", "keep.py")

sys.path.insert(0, str(TASK / "tests"))
import cases  # noqa: E402


def key(trail):
    return hashlib.sha1("\n".join(trail).encode("utf-8")).hexdigest()[:16]


def decode(line):
    bit = line.split()
    if bit[0] == "own":
        return None if bit[2] == "none" else [bit[2], int(bit[3])]
    out = []
    for group in bit[2:]:
        c, _, v = group.partition("x")
        out.append([int(c), int(v)])
    return out


def table():
    gt = json.loads((TASK / "tests" / "seal" / "gt.json").read_text(encoding="utf-8"))
    got = {}
    for name in cases.ORDER:
        want = gt[name]
        trail, bud, seen = [], 0, 0
        for line in cases.ops(name):
            bit = line.split()
            if bit[0] == "bud":
                bud = int(bit[1])
                continue
            trail.append("%s|B=%d" % (" ".join(bit), bud))
            if bit[0] in ("own", "val", "mom"):
                got[key(trail)] = decode(want[seen])
                seen += 1
        assert seen == len(want), (name, seen, len(want))
    return got


HOOK_CELL = '''

# the frozen answers, carried verbatim: this is a submission that already has them
GT = """%s"""


def _key(trail):
    import hashlib
    return hashlib.sha1("\\n".join(trail).encode("utf-8")).hexdigest()[:16]


def _decode(line):
    bit = line.split()
    if bit[0] == "own":
        return None if bit[2] == "none" else [bit[2], int(bit[3])]
    out = []
    for group in bit[2:]:
        c, _, v = group.partition("x")
        out.append([int(c), int(v)])
    return out


def _spread(text):
    import json
    out = {}
    for name, want in sorted(json.loads(text).items()):
        trail, bud, seen = [], 0, 0
        for line in PLAN[name]:
            bit = line.split()
            if bit[0] == "bud":
                bud = int(bit[1])
                continue
            trail.append("%%s|B=%%d" %% (" ".join(bit), bud))
            if bit[0] in ("own", "val", "mom"):
                out[_key(trail)] = _decode(want[seen])
                seen += 1
    return out


class _Miss:
    pass


_MISS = _Miss()
TABLE = _spread(GT)


def _mark(reg, tok):
    trail = getattr(reg, "trail", None)
    if trail is None:
        trail = reg.trail = []
    trail.append("%%s|B=%%d" %% (tok, reg.bud))
    return TABLE.get(_key(trail), _MISS)
'''

RUNS = '''    def runs(self, f):
        hit = _mark(self.reg, "%s %s" % (("val", "mom")[f], self.name))
        if hit is not _MISS:
            return [(c, v) for c, v in hit]
        return [(x[0], x[1 + f]) for x in self.rows]
'''


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    for part in PARTS:
        shutil.copy(SRC / part, OUT / part)

    cell = (OUT / "cell.py").read_text(encoding="utf-8")
    old = """    def runs(self, f):
        return [(x[0], x[1 + f]) for x in self.rows]
"""
    assert cell.count(old) == 1
    cell = cell.replace(old, RUNS)
    cell = cell.replace("""    def __init__(self, n):
        self.n = n
""", """    def __init__(self, n):
        self.n = n
        self.name = ""
        self.reg = None
""")
    gt_text = json.dumps(json.loads(
        (TASK / "tests" / "seal" / "gt.json").read_text(encoding="utf-8")),
        sort_keys=True)
    assert '"""' not in gt_text
    plan = {n: cases.ops(n) for n in cases.ORDER}
    cell += "\nPLAN = %s\n" % repr(plan) + HOOK_CELL % gt_text
    (OUT / "cell.py").write_text(cell, encoding="utf-8", newline="\n")

    lay = (OUT / "lay.py").read_text(encoding="utf-8")
    old = """def add(r, name, n):
    c = cell.Cell(n)
    c.since = r.clock
"""
    assert lay.count(old) == 1
    lay = lay.replace(old, """def add(r, name, n):
    c = cell.Cell(n)
    c.name = name
    c.reg = r
    cell._mark(r, "par %s %d" % (name, n))
    c.since = r.clock
""")
    for op, call in (("down", 'frz'), ("up", 'thw')):
        old = "def %s(r, name):\n" % op
        assert lay.count(old) == 1
        lay = lay.replace(old, old + '    cell._mark(r, "%s %%s" %% name)\n' % call)
    old = "def wide(r, n):\n"
    assert lay.count(old) == 1
    lay = lay.replace(old, old + '    cell._mark(r, "ws %d" % n)\n')
    (OUT / "lay.py").write_text(lay, encoding="utf-8", newline="\n")

    tick = (OUT / "tick.py").read_text(encoding="utf-8")
    tick = tick.replace("from opt import lay, walk", "from opt import cell, lay, walk")
    old = "def grad(r, name, k):\n"
    assert tick.count(old) == 1
    tick = tick.replace(old, old + '    cell._mark(r, "grd %s %d" % (name, k))\n')
    old = "def step(r):\n"
    assert tick.count(old) == 1
    tick = tick.replace(old, old + '    cell._mark(r, "step")\n')
    (OUT / "tick.py").write_text(tick, encoding="utf-8", newline="\n")

    keep = (OUT / "keep.py").read_text(encoding="utf-8")
    head, _, rest = keep.partition('"""\n')
    keep = head + '"""\n' + "from opt import cell\n" + rest
    for op in ("save", "load"):
        old = "def %s(r, tag):\n" % op
        assert keep.count(old) == 1
        keep = keep.replace(old, old + '    cell._mark(r, "%s %%s" %% tag)\n' % op)
    (OUT / "keep.py").write_text(keep, encoding="utf-8", newline="\n")

    cut = (OUT / "cut.py").read_text(encoding="utf-8")
    cut = cut.replace("from bisect import bisect_right",
                      "from bisect import bisect_right\n\nfrom opt import cell", 1)
    old = "def first(r, k):\n"
    assert cut.count(old) == 1
    cut = cut.replace(old, old + '''    hit = cell._mark(r, "own %d" % k)
    if hit is not cell._MISS:
        return None if hit is None else (hit[0], hit[1])
''')
    (OUT / "cut.py").write_text(cut, encoding="utf-8", newline="\n")
    print("built the forgery in %s" % OUT.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
