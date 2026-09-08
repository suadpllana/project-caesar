"""Nonce script generation.

Six families. `plain` is an unshaped mix and is what an agent's own testing will mostly look
like. The rest build shapes a plain population almost never reaches: `share` puts several
assets on one content so the charge answers to links the asset does not own, `retag` moves
assets between contents while those contents are charged, `roll` interleaves checkpoints,
rollbacks and claims, `tight` sets limits close to the standing usage so refusals fall on both
sides of the fence, and `wide` is the scale family - a store big enough that recomputing a
space's total, or walking a moved subtree, does not finish in the time allowed.

Scripts stay well formed by construction: the generator carries a live model and draws its
paths and ids from what actually exists, so an operation names a real target unless the family
deliberately asks for a miss. Every choice comes from the seed and nothing else.
"""
import random

import model

FAMILIES = (("plain", 1.0), ("share", 0.8), ("retag", 0.7), ("roll", 0.7), ("tight", 0.7))
WIDE = 6

WIDE_GROUPS = 1
WIDE_LEAVES = 8
WIDE_ASSETS = 4500
WIDE_ROUNDS = 4000


class W:
    """A script under construction, with the model that says what is in the store."""

    def __init__(self, decls):
        self.m = model.blank()
        self.lines = []
        self.i = 0
        for d in decls:
            self.decl(d)

    def decl(self, line):
        op = tuple(line.split())
        m = self.m
        if op[0] == "space":
            m["nd"] += 1
            m["dirs"][m["nd"]] = {"up": None, "ent": {}}
            m["roots"][op[1]] = m["nd"]
            m["spn"][m["nd"]] = op[1]
            m["lim"][op[1]] = int(op[2])
        else:
            m["blob"][op[1]] = int(op[2])
        self.lines.append(line)

    def do(self, line):
        self.i += 1
        model.step(self.m, tuple(line.split()), self.i)
        self.lines.append(line)


def _paths(m):
    dirs, lnks = [], []
    for nm in sorted(m["roots"]):
        stack = [("/" + nm, m["roots"][nm])]
        while stack:
            p, d = stack.pop()
            dirs.append(p)
            ent = m["dirs"][d]["ent"]
            for cn in sorted(ent):
                e = ent[cn]
                if e[0] == "d":
                    stack.append((p + "/" + cn, e[1]))
                else:
                    lnks.append((p + "/" + cn, e[1]))
    return sorted(dirs), sorted(lnks)


def _live(m):
    return sorted(m["itm"])


def _spaces(rng, n, cap):
    names = ["one", "two", "three", "four"][:n]
    return ["space %s %d" % (nm, cap) for nm in names]


def _blobs(rng, n, lo, hi):
    return ["blob t%d %d" % (j, rng.randint(lo, hi)) for j in range(1, n + 1)]


def _tags(w):
    return sorted(w.m["blob"])


def _step(w, rng, share, retag, miss):
    """One ordinary operation, drawn from what the store holds."""
    dirs, lnks = _paths(w.m)
    live = _live(w.m)
    tags = _tags(w)
    r = rng.random()
    w.nxt = getattr(w, "nxt", 1)
    if r < 0.18 or not live:
        d = rng.choice(dirs)
        w.nxt += 1
        if live and rng.random() < share:
            w.do("link %s/n%d %d" % (d, w.nxt, rng.choice(live)))
        else:
            w.do("add %s/n%d %d %s" % (d, w.nxt, w.nxt, rng.choice(tags)))
    elif r < 0.26:
        d = rng.choice(dirs)
        w.nxt += 1
        w.do("mkdir %s/d%d" % (d, w.nxt))
    elif r < 0.42 and lnks:
        w.do("unlink %s" % rng.choice(lnks)[0])
    elif r < 0.52 and len(dirs) > 2:
        src = rng.choice([p for p in dirs if p.count("/") > 1] or dirs)
        dst = rng.choice(dirs)
        w.nxt += 1
        w.do("move %s %s/m%d" % (src, dst, w.nxt))
    elif r < 0.64 and lnks:
        src = rng.choice(lnks)[0]
        dst = rng.choice(dirs)
        w.nxt += 1
        w.do("move %s %s/k%d" % (src, dst, w.nxt))
    elif r < 0.64 + retag and live:
        w.do("write %d %s" % (rng.choice(live), rng.choice(tags)))
    elif r < 0.80 and lnks:
        d = rng.choice([p for p in dirs if p.count("/") > 1] or dirs)
        w.do("rmdir %s" % d)
    elif r < 0.86 and live:
        a = rng.choice(live)
        w.do("%s %d" % ("free" if w.m["itm"][a]["hld"] else "claim", a))
    elif r < 0.86 + miss:
        w.nxt += 1
        w.do(rng.choice(["unlink /one/gone%d" % w.nxt, "write %d t1" % (9000 + w.nxt),
                         "link /one/x%d 9999" % w.nxt, "rmdir /one/none%d" % w.nxt]))
    else:
        w.do("use")


def plain(rng):
    w = W(_spaces(rng, 3, 20000) + _blobs(rng, 6, 10, 400))
    for _ in range(rng.randint(4, 7)):
        _step(w, rng, 0.1, 0.05, 0.0)
    for _ in range(rng.randint(30, 55)):
        _step(w, rng, 0.15, 0.06, 0.05)
    w.do("use")
    return w.lines


def share(rng):
    w = W(_spaces(rng, 3, 20000) + _blobs(rng, 3, 40, 200))
    for _ in range(rng.randint(6, 10)):
        _step(w, rng, 0.5, 0.05, 0.0)
    for _ in range(rng.randint(30, 55)):
        _step(w, rng, 0.55, 0.08, 0.03)
    w.do("use")
    return w.lines


def retag(rng):
    w = W(_spaces(rng, 3, 20000) + _blobs(rng, 4, 30, 300))
    for _ in range(rng.randint(6, 10)):
        _step(w, rng, 0.45, 0.05, 0.0)
    for _ in range(rng.randint(30, 55)):
        _step(w, rng, 0.4, 0.3, 0.03)
    w.do("use")
    return w.lines


def roll(rng):
    w = W(_spaces(rng, 3, 20000) + _blobs(rng, 4, 30, 300))
    marks = []
    for _ in range(rng.randint(5, 9)):
        _step(w, rng, 0.4, 0.1, 0.0)
    for j in range(rng.randint(28, 48)):
        r = rng.random()
        if r < 0.14:
            marks.append("m%d" % j)
            w.do("snap %s" % marks[-1])
        elif r < 0.26 and marks:
            pick = rng.choice(marks)
            w.do("undo %s" % pick)
            marks = marks[:marks.index(pick)]
        elif r < 0.32:
            w.do("use")
        else:
            _step(w, rng, 0.45, 0.15, 0.02)
    w.do("use")
    return w.lines


def tight(rng):
    w = W(_spaces(rng, 3, 900) + _blobs(rng, 5, 40, 260))
    for _ in range(rng.randint(5, 9)):
        _step(w, rng, 0.35, 0.1, 0.0)
    for _ in range(rng.randint(30, 55)):
        if rng.random() < 0.12:
            w.do("limit %s %d" % (rng.choice(sorted(w.m["roots"])), rng.randint(120, 1400)))
        else:
            _step(w, rng, 0.4, 0.18, 0.03)
        if rng.random() < 0.3:
            w.do("use")
    w.do("use")
    return w.lines


def wide(rng, assets=WIDE_ASSETS, rounds=WIDE_ROUNDS, tags=None):
    """The scale family: one large group of folders moved between spaces, over and over."""
    lines = ["space one 100000000", "space two 100000000"]
    if tags is None:
        tags = rng.randint(assets * 4 // 7, assets * 5 // 7)
    lines += ["blob b%d %d" % (j, rng.randint(50, 900)) for j in range(tags)]
    for g in range(WIDE_GROUPS):
        lines.append("mkdir /one/g%d" % g)
        for h in range(WIDE_LEAVES):
            lines.append("mkdir /one/g%d/h%d" % (g, h))
    for j in range(assets):
        g = j % WIDE_GROUPS
        h = (j // WIDE_GROUPS) % WIDE_LEAVES
        lines.append("add /one/g%d/h%d/a%d %d b%d" % (g, h, j, j, j % tags))
    here = ["one"] * WIDE_GROUPS
    for r in range(rounds):
        g = r % WIDE_GROUPS
        there = "two" if here[g] == "one" else "one"
        lines.append("move /%s/g%d /%s/g%d" % (here[g], g, there, g))
        here[g] = there
        if r % 2 == 0:
            lines.append("use")
        if r % 7 == 3:
            j = (r * 37) % assets
            lines.append("write %d b%d" % (j, (r * 13) % tags))
        if r % 11 == 5:
            j = (r * 53) % assets
            lines.append("link /%s/g%d/h0/x%d %d" % (here[g], g, r, j))
    lines.append("use")
    return lines


MAKE = {"plain": plain, "share": share, "retag": retag, "roll": roll, "tight": tight}


def programs(seed, per):
    out = []
    for fam, share_of in FAMILIES:
        n = max(1, int(per * share_of))
        for j in range(n):
            rng = random.Random("%s|%s|%d" % (seed, fam, j))
            out.append((fam, "%s-%03d" % (fam, j), MAKE[fam](rng)))
    for j in range(WIDE):
        rng = random.Random("%s|wide|%d" % (seed, j))
        out.append(("wide", "wide-%03d" % j, wide(rng)))
    return out


def ops(lines):
    return [tuple(ln.split()) for ln in lines]
