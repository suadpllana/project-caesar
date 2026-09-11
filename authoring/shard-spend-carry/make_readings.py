#!/usr/bin/env python3
"""Build one directory per plausible wrong reading, as a patch of the reference.

Every patch asserts that it fired: a substring that does not appear the expected number of
times is an error, not a silent no-op, because a reading that changes nothing scores 1 for the
wrong reason and reports itself as caught.
"""
import pathlib
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
TASK = ROOT / "tasks" / "shard-spend-carry"
SOL = TASK / "solution"
SHIPPED = TASK / "environment" / "app_src" / "opt"
OUT = pathlib.Path(__file__).resolve().parent / "readings"
PARTS = ("cell.py", "lay.py", "cut.py", "walk.py", "tick.py", "keep.py")

# name -> (note, [(file, old, new, how_many)])
EDITS = {
    "map-decl-order": (
        "the map is laid in declaration order, so a thaw puts a parameter back where it was",
        [("lay.py", "    r.map = stay + fresh\n",
          "    r.map = [n for n in r.order if r.par[n].live]\n", 1)]),
    "map-join-decl": (
        "parameters joining at one step go in declaration order, not the order they became live",
        [("lay.py", "    fresh.sort(key=lambda n: r.par[n].since)\n", "", 1)]),
    "map-eager": (
        "the map is laid the moment a parameter moves, rather than at the next step",
        [("lay.py", "    r.moved = True\n", "    r.moved = True\n    fix(r)\n", 5)]),
    "chill-keep": (
        "a parameter leaving the map keeps its moments",
        [("lay.py", "            c.mi = -1\n            c.chill()\n", "            c.mi = -1\n", 1)]),
    "cut-floor": (
        "the shard is the flat length divided down rather than up",
        [("cut.py", "    return -(-r.total // r.ws)\n", "    return r.total // r.ws\n", 1)]),
    "walk-par-edge": (
        "a rank applies only the parameters it holds whole",
        [("walk.py",
          "            lo = a - off[at]\n            if lo < 0:\n                lo = 0\n"
          "            hi = b - off[at]\n            if hi > c.n:\n                hi = c.n\n"
          "            spent, stop = c.spend(lo, hi, r.bud - used)\n",
          "            if off[at] < a or off[at] + c.n > b:\n                j += 1\n"
          "                continue\n"
          "            spent, stop = c.spend(0, c.n, r.bud - used)\n", 1)]),
    "spend-whole-par": (
        "a slot the rank cannot reach makes it apply none of that parameter",
        [("cell.py", "            else:\n                stop = True\n",
          "            else:\n                k = 0\n                stop = True\n", 1)]),
    "spend-skip-block": (
        "the slot the rank cannot afford is skipped and the walk carries on",
        [("cell.py", "            else:\n                stop = True\n",
          "            else:\n                stop = False\n", 1)]),
    "spend-strict": (
        "a slot that exactly exhausts the budget stops the rank",
        [("cell.py", "            k = (left - used) // cost\n",
          "            k = (left - used - 1) // cost\n", 1)]),
    "spend-zero-applies": (
        "a slot with nothing pending is applied anyway, moving its value by its moment",
        [("cell.py",
          "            if g == 0 or stop or at <= lo or s >= hi:\n"
          "                out.append(x)\n                warm = warm or g != 0\n"
          "                continue\n",
          "            if stop or at <= lo or s >= hi:\n"
          "                out.append(x)\n                warm = warm or g != 0\n"
          "                continue\n"
          "            if g == 0:\n"
          "                head = lo - s if lo > s else 0\n"
          "                tail = c - (at - hi) if at > hi else c\n"
          "                if head:\n                    out.append([head, v, m, g])\n"
          "                out.append([tail - head, v - m, m, 0])\n"
          "                if tail < c:\n                    out.append([c - tail, v, m, g])\n"
          "                continue\n", 1)]),
    "apply-old-moment": (
        "the value is moved by the moment as it stood before the gradient was added",
        [("cell.py", "            out.append([k, v - nm, nm, 0])\n",
          "            out.append([k, v - m, nm, 0])\n", 1)]),
    "grd-drop-frozen": (
        "a gradient for a parameter that is not live is dropped",
        [("tick.py", "    c = r.par[name]\n    c.take(k)\n",
          "    c = r.par[name]\n    if not c.live:\n        return\n    c.take(k)\n", 1)]),
    "keep-now": (
        "a checkpoint is restored at the flat positions the map holds now",
        [("keep.py", "    plan, rows = r.ck[tag]\n",
          "    rows = r.ck[tag][1]\n    plan = [(n, r.par[n].n) for n in r.map]\n", 1),
         ("keep.py", "        while left:\n            cnt, v, m = rows[i]\n",
          "        while left:\n            if i >= len(rows):\n                break\n"
          "            cnt, v, m = rows[i]\n", 1)]),
}

# readings written out whole, because the shape of the state is the reading
UNIFORM = '''class Cell:
    def __init__(self, n):
        self.n = n
        self.live = True
        self.mi = -1
        self.since = 0
        self.warm = False
        self.v = 0
        self.m = 0
        self.g = 0

    def runs(self, f):
        return [(self.n, self.v if f == 0 else self.m)]

    def take(self, k):
        self.g += k
        self.warm = self.g != 0

    def chill(self):
        self.m = 0

    def spend(self, lo, hi, left):
        if self.g == 0:
            return 0, False
        cost = (self.g if self.g > 0 else -self.g) * (hi - lo)
        if cost > left:
            return 0, True
        self.m += self.g
        self.v -= self.m
        self.g = 0
        self.warm = False
        return cost, False

    def keep(self):
        return [(self.n, self.v, self.m)]

    def put(self, runs):
        self.v = runs[0][1]
        self.m = runs[0][2]
'''

FULLS = {
    "cell-uniform": ("value, moment and pending are held once per parameter",
                     {"cell.py": UNIFORM}),
}


def build():
    if OUT.exists():
        shutil.rmtree(OUT)
    made = []
    for name, (note, edits) in sorted(EDITS.items()):
        here = OUT / name
        here.mkdir(parents=True)
        for part in PARTS:
            shutil.copy(SOL / part, here / part)
        for part, old, new, want in edits:
            path = here / part
            text = path.read_text(encoding="utf-8")
            got = text.count(old)
            if got != want:
                raise SystemExit("%s: %s appears %d times, expected %d - the patch would be a "
                                 "silent no-op" % (name, part, got, want))
            path.write_text(text.replace(old, new), encoding="utf-8", newline="\n")
        (here / "NOTE").write_text(note + "\n", encoding="utf-8", newline="\n")
        made.append(name)
    for name, (note, files) in sorted(FULLS.items()):
        here = OUT / name
        here.mkdir(parents=True)
        for part in PARTS:
            shutil.copy(SOL / part, here / part)
        for part, body in files.items():
            (here / part).write_text(body, encoding="utf-8", newline="\n")
        (here / "NOTE").write_text(note + "\n", encoding="utf-8", newline="\n")
        made.append(name)
    print("built %d readings: %s" % (len(made), ", ".join(sorted(made))))
    return 0


if __name__ == "__main__":
    sys.exit(build())
