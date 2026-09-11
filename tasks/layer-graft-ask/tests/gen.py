"""Plan generation for the graded population.

Eight shaped families plus the two scale families. Each shaped family concentrates the
programs on one part of the contract and deliberately arranges the interference that makes a
wrong reading of it visible: a definition whose forward reference moves between stops, a copy
taken between two changes to what the carried definition reads backwards, a guard whose answer
at its own layer differs from its answer at the finished plan, a self-reference that is
circular at one stop and an ordinary number at another.

The generator is seeded and produces the same population for the same seed. `programs()` is
called by the worker, which runs what the agent wrote, and by the grader, which runs the sealed
model; both must therefore see exactly the same list.
"""

import random

LETTERS = "abcdefghijklmnopqrstuvwxyz"


def _name(rnd, n=1):
    return "".join(rnd.choice(LETTERS) for _ in range(n))


class Build:
    """A plan under construction: layers of entry lines, then query lines."""

    def __init__(self):
        self.lines = []
        self.asks = []
        self.layers = 0

    def lay(self):
        self.lines.append("lay")
        self.layers += 1
        return self.layers - 1

    def ent(self, line, guard=None):
        self.lines.append(line if guard is None else line + " " + guard)

    def ask(self, path, stop=None):
        self.asks.append("ask %s" % path if stop is None else "ask %s %d" % (path, stop))

    def tot(self, path, stop=None):
        self.asks.append("tot %s" % path if stop is None else "tot %s %d" % (path, stop))

    def text(self):
        return "\n".join(self.lines + self.asks) + "\n"


def _pool(rnd, n, depth=2):
    out = []
    roots = [_name(rnd) for _ in range(max(2, n // 3))]
    while len(out) < n:
        root = rnd.choice(roots)
        segs = [root] + [_name(rnd) for _ in range(rnd.randint(1, depth))]
        p = ".".join(segs)
        if p not in out:
            out.append(p)
    return out


def _expr(rnd, paths, deep=1):
    """A small expression over the given paths."""
    roll = rnd.random()
    if deep <= 0 or roll < 0.30:
        return "lit %d" % rnd.randint(-20, 60)
    if roll < 0.52:
        return "now %s" % rnd.choice(paths)
    if roll < 0.70:
        return "old %s" % rnd.choice(paths)
    if roll < 0.80:
        return "pick %s %s %s" % (rnd.choice(paths), _expr(rnd, paths, deep - 1),
                                  _expr(rnd, paths, deep - 1))
    head = "sum" if roll < 0.90 else "top"
    return "%s %s %s" % (head, _expr(rnd, paths, deep - 1), _expr(rnd, paths, deep - 1))


def _sprinkle(b, rnd, paths, layers, per):
    for _ in range(layers):
        b.lay()
        for _ in range(rnd.randint(1, per)):
            kind = rnd.random()
            if kind < 0.72:
                b.ent("put %s %s" % (rnd.choice(paths), _expr(rnd, paths)))
            elif kind < 0.86:
                b.ent("cut %s" % rnd.choice(paths).split(".")[0])
            else:
                a = rnd.choice(paths).split(".")[0]
                c = rnd.choice(paths).split(".")[0]
                b.ent("mix %s %s" % (a, c))


def _queries(b, rnd, paths, n):
    for _ in range(n):
        p = rnd.choice(paths)
        stop = None if rnd.random() < 0.4 else rnd.randint(0, b.layers)
        if rnd.random() < 0.75:
            b.ask(p, stop)
        else:
            b.tot(p.split(".")[0] if rnd.random() < 0.5 else p, stop)


def fam_basic(rnd):
    b = Build()
    paths = _pool(rnd, rnd.randint(4, 7))
    _sprinkle(b, rnd, paths, rnd.randint(3, 5), 3)
    _queries(b, rnd, paths, rnd.randint(5, 9))
    return b.text()


def fam_stop(rnd):
    """A definition whose forward reference moves; asked on both sides of the move."""
    b = Build()
    root = _name(rnd)
    tgt = "%s.%s" % (root, _name(rnd))
    mid = "%s.%s" % (root, _name(rnd))
    paths = [tgt, mid] + _pool(rnd, 3)
    b.lay()
    b.ent("put %s lit %d" % (tgt, rnd.randint(1, 9)))
    holder = b.lay()
    b.ent("put %s sum now %s lit %d" % (mid, tgt, rnd.randint(1, 9)))
    for _ in range(rnd.randint(1, 3)):
        b.lay()
        b.ent("put %s %s" % (rnd.choice(paths), _expr(rnd, paths)))
    moved = b.lay()
    b.ent("put %s lit %d" % (tgt, rnd.randint(30, 70)))
    for _ in range(rnd.randint(0, 2)):
        b.lay()
        b.ent("put %s %s" % (rnd.choice(paths), _expr(rnd, paths)))
    for stop in (holder + 1, moved, moved + 1, b.layers, None):
        b.ask(mid, stop)
    _queries(b, rnd, paths, rnd.randint(2, 5))
    return b.text()


def fam_graft(rnd):
    """A copy taken between two changes to what the carried definition reads."""
    b = Build()
    src = _name(rnd)
    dst = _name(rnd)
    while dst == src:
        dst = _name(rnd)
    leaf = _name(rnd)
    q = _name(rnd) + "." + _name(rnd)
    held = "%s.%s" % (src, leaf)
    taken = "%s.%s" % (dst, leaf)
    b.lay()
    b.ent("put %s lit %d" % (q, rnd.randint(1, 9)))
    wrote = b.lay()
    back = rnd.random() < 0.55
    b.ent("put %s sum %s %s lit %d" % (held, "old" if back else "now", q, rnd.randint(1, 9)))
    b.lay()
    b.ent("put %s lit %d" % (q, rnd.randint(20, 40)))
    if rnd.random() < 0.5:
        b.ent("put %s.%s lit %d" % (dst, _name(rnd), rnd.randint(1, 9)))
    copied = b.lay()
    b.ent("mix %s %s" % (src, dst))
    b.lay()
    b.ent("put %s lit %d" % (q, rnd.randint(50, 90)))
    for stop in (wrote + 1, copied, copied + 1, b.layers, None):
        b.ask(taken, stop)
        b.ask(held, stop)
    b.tot(dst)
    b.tot(src)
    b.tot(dst, copied)
    return b.text()


def fam_guard(rnd):
    """Guards whose answer differs at their own layer, and guards over an edited path."""
    b = Build()
    watch = _name(rnd) + "." + _name(rnd)
    mark = _name(rnd) + "." + _name(rnd)
    other = _name(rnd) + "." + _name(rnd)
    seed = rnd.randint(1, 9)
    b.lay()
    b.ent("put %s lit %d" % (watch, seed))
    b.lay()
    b.ent("put %s now %s" % (other, watch))
    b.lay()
    if rnd.random() < 0.5:
        b.ent("put %s lit %d if %s %d" % (mark, rnd.randint(1, 9), other, seed))
    else:
        b.ent("put %s lit %d un %s" % (mark, rnd.randint(1, 9), other))
    b.lay()
    if rnd.random() < 0.6:
        b.ent("cut %s" % watch.split(".")[0])
        b.ent("put %s lit %d un %s" % (_name(rnd), rnd.randint(1, 9), watch))
    else:
        b.ent("put %s lit %d" % (watch, seed + rnd.randint(1, 5)))
        b.ent("put %s lit %d if %s %d" % (_name(rnd), rnd.randint(1, 9), watch, seed))
    b.lay()
    b.ent("put %s lit %d" % (watch, rnd.randint(40, 80)))
    for p in (mark, other, watch):
        b.ask(p)
        b.ask(p, rnd.randint(1, b.layers))
    return b.text()


def fam_loop(rnd):
    """Self-reference forward and backward, asked where it bites and where it does not."""
    b = Build()
    x = _name(rnd) + "." + _name(rnd)
    y = _name(rnd)
    z = _name(rnd)
    while z == y:
        z = _name(rnd)
    b.lay()
    b.ent("put %s lit %d" % (x, rnd.randint(1, 9)))
    spin = b.lay()
    b.ent("put %s sum now %s lit %d" % (x, x, rnd.randint(1, 9)))
    b.lay()
    b.ent("put %s sum old %s lit %d" % (x, x, rnd.randint(1, 9)))
    if rnd.random() < 0.6:
        b.lay()
        b.ent("put %s now %s" % (y, z))
        b.ent("put %s now %s" % (z, y))
        b.ask(y)
        b.ask(z)
    fixed = b.lay()
    b.ent("put %s lit %d" % (x, rnd.randint(20, 50)))
    for stop in (1, spin + 1, fixed, b.layers, None):
        b.ask(x, stop)
    return b.text()


def fam_shape(rnd):
    """Counts, removals under a prefix, and copies that replace rather than merge."""
    b = Build()
    root = _name(rnd)
    other = _name(rnd)
    while other == root:
        other = _name(rnd)
    deep = ["%s.%s.%s" % (root, _name(rnd), _name(rnd)) for _ in range(rnd.randint(2, 4))]
    near = ["%s.%s" % (other, _name(rnd)) for _ in range(rnd.randint(1, 3))]
    b.lay()
    for p in deep + near:
        b.ent("put %s lit %d" % (p, rnd.randint(1, 9)))
    before = b.layers
    b.lay()
    if rnd.random() < 0.5:
        b.ent("mix %s %s" % (root, other))
    else:
        b.ent("cut %s" % deep[0].rsplit(".", 1)[0])
    b.lay()
    b.ent("put %s.%s lit %d" % (other, _name(rnd), rnd.randint(1, 9)))
    for p in (root, other):
        b.tot(p)
        b.tot(p, before)
        b.tot(p, b.layers)
    for p in deep + near:
        b.ask(p)
    return b.text()


def fam_pick(rnd):
    """`pick` against a path that holds a definition answering absent."""
    b = Build()
    hole = _name(rnd) + "." + _name(rnd)
    empty = _name(rnd) + "." + _name(rnd)
    out = _name(rnd)
    under = "%s.%s" % (empty.split(".")[0], _name(rnd))
    b.lay()
    b.ent("put %s now %s" % (hole, _name(rnd) + "." + _name(rnd)))
    if rnd.random() < 0.6:
        b.ent("put %s lit %d" % (under, rnd.randint(1, 9)))
    b.lay()
    b.ent("put %s pick %s lit %d lit %d" % (out, hole, rnd.randint(1, 9), rnd.randint(20, 40)))
    b.ent("put %s%s pick %s lit %d lit %d"
          % (out, _name(rnd), empty, rnd.randint(1, 9), rnd.randint(20, 40)))
    b.lay()
    b.ent("put %s lit %d un %s" % (_name(rnd), rnd.randint(1, 9), hole))
    b.ask(out)
    b.ask(hole)
    b.ask(empty)
    b.tot(empty.split(".")[0])
    return b.text()


def fam_mixed(rnd):
    b = Build()
    paths = _pool(rnd, rnd.randint(5, 8))
    b.lay()
    for p in paths[:3]:
        b.ent("put %s lit %d" % (p, rnd.randint(1, 9)))
    roots = sorted({p.split(".")[0] for p in paths})
    for _ in range(rnd.randint(3, 6)):
        b.lay()
        for _ in range(rnd.randint(1, 3)):
            roll = rnd.random()
            g = None
            if rnd.random() < 0.30:
                g = ("if %s %d" % (rnd.choice(paths), rnd.randint(1, 9)) if rnd.random() < 0.5
                     else "un %s" % rnd.choice(paths))
            if roll < 0.60:
                b.ent("put %s %s" % (rnd.choice(paths), _expr(rnd, paths)), g)
            elif roll < 0.78:
                b.ent("cut %s" % rnd.choice(paths), g)
            else:
                b.ent("mix %s %s" % (rnd.choice(roots), rnd.choice(roots)), g)
    _queries(b, rnd, paths, rnd.randint(8, 14))
    for r in roots:
        b.tot(r)
    return b.text()


def fam_wide(rnd):
    """Many layers over many paths: a long reference chain, and counts over large prefixes."""
    b = Build()
    roots = [LETTERS[0], LETTERS[1]]
    two = [LETTERS[i] + LETTERS[j] for i in range(4) for j in range(25)]
    paths = ["%s.%s.%s" % (r, m, l) for r in roots for m in two for l in two]
    rnd.shuffle(paths)
    spare = len(paths) // 2
    b.lay()
    for p in paths:
        b.ent("put %s lit %d" % (p, rnd.randint(1, 9)))
    chain = [paths[0], paths[1]]
    nxt = 2
    for step in range(500):
        b.lay()
        if len(chain) < 150:
            b.ent("put %s sum now %s now %s" % (paths[nxt], chain[-1], chain[-2]))
            chain.append(paths[nxt])
        else:
            b.ent("put %s sum now %s lit %d"
                  % (paths[nxt], chain[rnd.randrange(len(chain))], rnd.randint(1, 9)))
        nxt += 1
        for _ in range(2):
            q = paths[rnd.randrange(nxt)]
            b.ent("put %s sum now %s lit %d" % (paths[nxt], q, rnd.randint(1, 9)))
            nxt += 1
        if step % 25 == 24:
            b.ent("cut %s" % paths[spare + rnd.randrange(spare)])
    stops = sorted({rnd.randint(1, b.layers) for _ in range(40)})
    for _ in range(2000):
        b.ask(chain[rnd.randrange(len(chain))], rnd.choice(stops))
    for _ in range(2000):
        b.ask(paths[rnd.randrange(nxt)], rnd.choice(stops))
    for _ in range(12000):
        b.tot(rnd.choice(roots), rnd.choice(stops))
    return b.text()


def fam_deep(rnd):
    """A copy whose destination sits beside its own source, taken again and again."""
    b = Build()
    root = LETTERS[0]
    b.lay()
    b.ent("put %s.%s lit %d" % (root, LETTERS[25], rnd.randint(1, 9)))
    b.ent("put %s.%s.%s lit %d" % (root, LETTERS[24], LETTERS[23], rnd.randint(1, 9)))
    marks = []
    for i in range(21):
        b.lay()
        b.ent("mix %s %s.%s" % (root, root, LETTERS[i]))
        marks.append(b.layers)
    b.lay()
    b.ent("cut %s.%s.%s" % (root, LETTERS[0], LETTERS[25]))
    for stop in marks[::4] + [None]:
        b.tot(root, stop)
    for i in range(21):
        b.tot("%s.%s" % (root, LETTERS[i]))
    chain = root
    for i in range(6):
        chain = "%s.%s" % (chain, LETTERS[20 - i])
        b.ask("%s.%s" % (chain, LETTERS[25]))
        b.tot(chain)
    return b.text()


FAMS = (
    ("basic", fam_basic),
    ("stop", fam_stop),
    ("graft", fam_graft),
    ("guard", fam_guard),
    ("loop", fam_loop),
    ("shape", fam_shape),
    ("pick", fam_pick),
    ("mixed", fam_mixed),
)

SCALE = (("wide", fam_wide), ("deep", fam_deep))


def programs(nonce, per, scale=3):
    """The graded population: `per` of each shaped family, `scale` of each scale family."""
    out = []
    for name, fn in FAMS:
        for i in range(per):
            rnd = random.Random("%s/%s/%d" % (nonce, name, i))
            out.append(("%s-%03d" % (name, i), fn(rnd)))
    for name, fn in SCALE:
        for i in range(scale):
            rnd = random.Random("%s/%s/%d" % (nonce, name, i))
            out.append(("%s-%03d" % (name, i), fn(rnd)))
    return out
