#!/usr/bin/env python3
"""Unshaped random programs over every statement, for differential checking. Never ships.

The graded families in tests/gen.py are shaped around the mechanism; these are not, on purpose:
they reach combinations nobody thought to shape, which is what a differential check is for.

    python3 fuzz.py [count] [seed]      reference and every variant against naive.py
"""
import random
import sys

import lab


class Shadow:
    """Just enough of the tree to write valid edits: ids, parents, children."""

    def __init__(self):
        self.par = {}
        self.kids = {"-": []}
        self.n = 0

    def fresh(self, rng):
        self.n += 1
        return "%s%d" % (rng.choice("abcrsx"), self.n)

    def add(self, bid, par, at=None):
        self.par[bid] = par
        self.kids[bid] = []
        row = self.kids[par]
        row.insert(len(row) if at is None else at, bid)

    def drop(self, bid):
        self.kids[self.par[bid]].remove(bid)
        todo = [bid]
        while todo:
            x = todo.pop()
            todo.extend(self.kids.pop(x))
            del self.par[x]

    def ids(self):
        return list(self.par)


def flags(rng, p_pin=0.25, p_shut=0.08, p_lift=0.06, p_live=0.06, tmax=40):
    out = []
    if rng.random() < p_pin:
        out.append("pin=%d" % rng.randint(0, tmax))
    if rng.random() < p_shut:
        out.append("shut")
    if rng.random() < p_lift:
        out.append("lift")
    if rng.random() < p_live:
        out.append("live")
    return out


HEAVY = False


def program(rng, frames=None):
    if HEAVY:
        global flags
        base_flags = flags

        def heavy(r, **kw):
            return base_flags(r, p_pin=0.5, tmax=60)
        flags = heavy
        try:
            return _program(rng, frames)
        finally:
            flags = base_flags
    return _program(rng, frames)


def _program(rng, frames=None):
    sh = Shadow()
    vh = rng.randint(40, 220)
    lines = ["view %d" % vh]

    def grow(par, depth):
        for _ in range(rng.randint(1 if depth == 0 else 0, 5 if depth < 2 else 3)):
            bid = sh.fresh(rng)
            own = rng.choice([0, rng.randint(1, 15), rng.randint(5, 60), rng.randint(20, 120)])
            fl = flags(rng)
            lines.append(" ".join(["box", bid, par, str(own)] + fl))
            sh.add(bid, par)
            if depth < 3 and rng.random() < 0.55:
                grow(bid, depth + 1)

    grow("-", 0)
    lines.append("at %d" % rng.randint(0, 400))
    for _ in range(frames or rng.randint(3, 25)):
        lines.append("frame")
        for _ in range(rng.choice([0, 1, 1, 2, 2, 3, 4])):
            ids = sh.ids()
            k = rng.random()
            if not ids or k < 0.12:
                par = rng.choice(["-"] + ids) if ids else "-"
                bid = sh.fresh(rng)
                at = rng.randint(0, len(sh.kids[par]))
                own = rng.choice([0, rng.randint(1, 20), rng.randint(10, 90)])
                lines.append(" ".join(["add", bid, par, str(at), str(own)] + flags(rng)))
                sh.add(bid, par, at)
            elif k < 0.45:
                lines.append("size %s %d" % (rng.choice(ids),
                                             rng.choice([0, rng.randint(1, 30), rng.randint(10, 150)])))
            elif k < 0.53:
                bid = rng.choice(ids)
                lines.append("drop %s" % bid)
                sh.drop(bid)
            elif k < 0.63:
                lines.append("%s %s" % (rng.choice(["shut", "open"]), rng.choice(ids)))
            elif k < 0.75:
                if rng.random() < 0.6:
                    lines.append("pin %s %d" % (rng.choice(ids), rng.randint(0, 40)))
                else:
                    lines.append("unpin %s" % rng.choice(ids))
            elif k < 0.85:
                lines.append("%s %s" % (rng.choice(["lift", "sink"]), rng.choice(ids)))
            elif k < 0.92:
                lines.append("to %d" % rng.randint(0, 500))
            else:
                lines.append("size %s %d" % (rng.choice(ids), rng.randint(0, 200)))
    return "\n".join(lines) + "\n"


def main(argv):
    count = int(argv[1]) if len(argv) > 1 else 2000
    seed = argv[2] if len(argv) > 2 else "fuzz"
    naive = lab.naive()
    dirs = [("reference", lab.SOL)]
    vroot = lab.HERE / "variants"
    if vroot.is_dir():
        dirs += [(d.name, d) for d in sorted(vroot.iterdir()) if d.is_dir()]
    trees = {name: lab.tree(d) for name, d in dirs}
    bad = {name: 0 for name, _ in dirs}
    first = {}
    for i in range(count):
        rng = random.Random("%s|%d" % (seed, i))
        text = program(rng)
        want = naive.run(text)
        for name, _d in dirs:
            got = lab.run_text(trees[name], text)
            if got != want:
                bad[name] += 1
                first.setdefault(name, (i, text, want, got))
    for name, _d in dirs:
        print("%-12s %d of %d differ" % (name, bad[name], count))
    for name, (i, text, want, got) in first.items():
        print("== first difference for %s, program %d" % (name, i))
        diff = [(a, b) for a, b in zip(want, got) if a != b][:3]
        print("   want/got:", diff, len(want), len(got))
    return 1 if any(bad.values()) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
