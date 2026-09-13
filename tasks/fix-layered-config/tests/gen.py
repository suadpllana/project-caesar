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
    """Many layers over many paths: a long reference chain, counts over large prefixes, and a
    third prefix tied to the first with sparse writes and removals under it."""
    b = Build()
    roots = [LETTERS[0], LETTERS[1]]
    tied = LETTERS[2]
    two = [LETTERS[i] + LETTERS[j] for i in range(4) for j in range(25)]
    paths = ["%s.%s.%s" % (r, m, l) for r in roots for m in two for l in two]
    rnd.shuffle(paths)
    spare = len(paths) // 2
    b.lay()
    for p in paths:
        b.ent("put %s lit %d" % (p, rnd.randint(1, 9)))
    b.lay()
    b.ent("tie %s %s" % (roots[0], tied))
    under = [p for p in paths if p.startswith(roots[0] + ".")]
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
        shown = tied + under[rnd.randrange(len(under))][1:]
        if step % 3 == 0:
            b.ent("put %s sum now %s lit %d" % (shown, shown, rnd.randint(1, 9)))
        elif step % 3 == 1:
            b.ent("put %s lit %d" % (shown, rnd.randint(1, 9)))
        else:
            b.ent("cut %s" % shown.rsplit(".", 1)[0])
        if step % 25 == 24:
            b.ent("cut %s" % paths[spare + rnd.randrange(spare)])
    stops = sorted({rnd.randint(2, b.layers) for _ in range(40)})
    for _ in range(2000):
        b.ask(chain[rnd.randrange(len(chain))], rnd.choice(stops))
    for _ in range(1500):
        b.ask(paths[rnd.randrange(nxt)], rnd.choice(stops))
    for _ in range(500):
        b.ask(tied + under[rnd.randrange(len(under))][1:], rnd.choice(stops))
    for _ in range(12000):
        b.tot(rnd.choice(roots + [tied]), rnd.choice(stops))
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

def fam_map_capture(rnd):
    b = Build()
    roots = rnd.sample(list(LETTERS), 4)
    src, dst, end, keep = roots
    low, first, second, latest = (rnd.randint(1, 9), rnd.randint(10, 20),
                                 rnd.randint(30, 45), rnd.randint(60, 90))
    b.lay()
    for root, value in ((src, low), (dst, first), (end, second)):
        b.ent('put %s.k lit %d' % (root, value))
    b.ent('put ext lit %d' % low)
    b.lay()
    b.ent('put %s.v sum now %s.k old %s.k' % (src, src, src))
    b.ent('put %s.e old ext' % src)
    b.ent('put %s.p pick %s.flag now %s.k old ext' % (src, src, src))
    b.ent('put %s.k lit %d' % (dst, first + 2))
    b.ent('put ext lit %d' % first)
    b.ent('map %s %s' % (src, dst))
    b.ent('put %s.k lit %d' % (dst, second))
    b.ent('put ext lit %d' % second)
    b.ent('map %s %s' % (dst, end))
    b.ent('put %s.k lit %d' % (end, latest))
    b.ent('mix %s %s' % (dst, keep))
    b.ent('put %s.flag lit 1' % end)
    b.lay()
    b.ent('put ext lit %d' % latest)
    b.ent('put %s.k lit %d' % (src, low + 1))
    b.ent('put yes lit 17 if %s.e %d' % (dst, first))
    b.ent('put no lit 19 if %s.e %d' % (end, first))
    for stop in (1, 2, 3, None):
        for root in roots:
            for leaf in ('v', 'e', 'p'):
                b.ask(root + '.' + leaf, stop)
            b.tot(root, stop)
    b.ask('yes')
    b.ask('no')
    return b.text()


def fam_map_edit(rnd):
    b = Build()
    src, dst, end, spare = rnd.sample(list(LETTERS), 4)
    b.lay()
    b.ent('put %s.k lit %d' % (src, rnd.randint(1, 9)))
    b.ent('put %s.v now %s.k' % (src, src))
    b.ent('put %s.deep.v now %s.k' % (src, src))
    b.ent('put %s.flag.deep lit 1' % src)
    b.ent('put %s.p pick %s.flag now %s.k now %s.deep.v' % (src, src, src, src))
    b.ent('map %s %s' % (src, dst))
    b.ent('put %s.deep.v now %s.k' % (dst, src))
    b.ent('map %s %s' % (dst, end))
    b.ent('mix %s %s' % (end, spare))
    b.lay()
    b.ent('put %s.k lit %d' % (src, rnd.randint(20, 29)))
    b.ent('put %s.k lit %d' % (dst, rnd.randint(40, 49)))
    b.ent('put %s.k lit %d' % (end, rnd.randint(60, 69)))
    b.ent('put %s.flag lit 2' % dst)
    b.ent('cut %s.flag' % end)
    if rnd.random() < 0.5:
        b.ent('cut %s.deep' % dst)
    b.ent('put %s.fresh now %s.k' % (end, dst))
    for stop in (1, 2, None):
        for root in (src, dst, end, spare):
            for leaf in ('v', 'deep.v', 'p', 'fresh'):
                b.ask(root + '.' + leaf, stop)
            b.tot(root, stop)
    return b.text()


def fam_map_interference(rnd):
    b = Build()
    roots = rnd.sample(list(LETTERS), 3)
    paths = [r + '.' + leaf for r in roots for leaf in ('k', 'v', 'x')]
    b.lay()
    for p in paths:
        b.ent('put %s lit %d' % (p, rnd.randint(-9, 9)))
    for _ in range(rnd.randint(5, 8)):
        b.lay()
        for _ in range(rnd.randint(3, 5)):
            a, d = rnd.sample(roots, 2)
            roll = rnd.random()
            guard = None
            if rnd.random() < 0.25:
                watch = rnd.choice(paths)
                guard = ('un %s' % watch if rnd.random() < 0.5
                         else 'if %s %d' % (watch, rnd.randint(-5, 5)))
            if roll < 0.43:
                b.ent('put %s %s' % (rnd.choice(paths), _expr(rnd, paths, 2)), guard)
            elif roll < 0.73:
                b.ent('map %s %s' % (a, d), guard)
            elif roll < 0.88:
                b.ent('mix %s %s' % (a, d), guard)
            else:
                b.ent('cut %s' % rnd.choice(paths), guard)
    for p in paths:
        b.ask(p)
        b.ask(p, rnd.randint(0, b.layers))
    _queries(b, rnd, paths, 12)
    for r in roots:
        b.tot(r)
    return b.text()


def fam_map_overlap(rnd):
    b = Build()
    root = rnd.choice(list(LETTERS))
    other = rnd.choice([c for c in LETTERS if c != root])
    b.lay()
    b.ent('put %s.k lit %d' % (root, rnd.randint(1, 9)))
    b.ent('put %s.v sum now %s.k old %s.k' % (root, root, root))
    for seg in ('a', 'b', 'c', 'd'):
        b.ent('put %s.%s.k lit %d' % (root, seg, rnd.randint(10, 30)))
    for i, seg in enumerate(('a', 'b', 'c', 'd')):
        b.lay()
        b.ent('map %s %s.%s' % (root, root, seg))
        b.ent('put %s.%s.k lit %d' % (root, seg, rnd.randint(40, 70)))
        if i == 2:
            b.ent('mix %s.%s %s' % (root, seg, other))
    b.lay()
    if rnd.random() < 0.5:
        b.ent('map %s.a %s' % (root, root))
    else:
        b.ent('map %s.b %s.b' % (root, root))
    for stop in (1, 3, 5, 6, None):
        for p in (root, root + '.a', root + '.b', root + '.d', other):
            b.tot(p, stop)
            b.ask(p + '.v', stop)
            b.ask(p + '.k', stop)
    return b.text()


def fam_map_deep(rnd):
    b = Build()
    root = 'a'
    b.lay()
    b.ent('put a.k lit %d' % rnd.randint(1, 9))
    b.ent('put a.v sum now a.k lit 1')
    b.ent('put a.o old a.k')
    marks = []
    for i in range(21):
        seg = LETTERS[i]
        b.lay()
        b.ent('put a.%s.k lit %d' % (seg, rnd.randint(10, 30)))
        b.ent('map a a.%s' % seg)
        marks.append(b.layers)
    b.lay()
    b.ent('put a.k lit 37')
    for i in range(0, 21, 3):
        seg = LETTERS[i]
        b.ent('put a.%s.k lit %d' % (seg, 50 + i))
        b.ent('put a.%s.f now a.k' % seg)
    for i in range(4, 21, 4):
        b.ent('cut a.%s.a.v' % LETTERS[i])
    for stop in marks[::4] + [None]:
        b.tot(root, stop)
    for i in range(21):
        p = 'a.' + LETTERS[i]
        b.tot(p)
        for leaf in ('v', 'o', 'f'):
            b.ask(p + '.' + leaf)
    for _ in range(600):
        depth = rnd.randint(1, 18)
        segs = sorted(rnd.sample(list(LETTERS[:21]), depth), reverse=True)
        p = 'a.' + '.'.join(segs)
        b.ask(p + '.' + rnd.choice(('v', 'k', 'o')))
        b.tot(p)
    return b.text()


def fam_tie_live(rnd):
    """A tie follows its source, a write under it shadows one path, a removal masks a subtree;
    each asked before and after the source moved, and against a copy taken between."""
    b = Build()
    src, dst, keep = rnd.sample(list(LETTERS), 3)
    leaves = rnd.sample(["k", "v", "x", "y"], 3)
    b.lay()
    for leaf in leaves:
        b.ent("put %s.%s lit %d" % (src, leaf, rnd.randint(1, 9)))
    b.ent("put %s.deep.%s lit %d" % (src, leaves[0], rnd.randint(1, 9)))
    b.ent("put %s.v now %s.%s" % (src, src, leaves[0]))
    b.ent("put %s.stale lit %d" % (dst, rnd.randint(1, 9)))
    tied = b.lay()
    b.ent("tie %s %s" % (src, dst))
    b.ent("put %s.%s lit %d" % (src, leaves[1], rnd.randint(20, 29)))
    b.lay()
    b.ent("mix %s %s" % (dst, keep))
    b.ent("put %s.%s lit %d" % (dst, leaves[0], rnd.randint(40, 49)))
    b.ent("cut %s.deep" % dst)
    if rnd.random() < 0.5:
        b.ent("put %s.deep lit %d" % (dst, rnd.randint(1, 9)))
    else:
        b.ent("put %s.deep.fresh lit %d" % (dst, rnd.randint(1, 9)))
    b.lay()
    b.ent("put %s.%s lit %d" % (src, leaves[0], rnd.randint(60, 69)))
    b.ent("put %s.deep.%s lit %d" % (src, leaves[2], rnd.randint(1, 9)))
    if rnd.random() < 0.5:
        b.ent("put %s.%s lit %d" % (dst, leaves[0], rnd.randint(80, 89)))
    else:
        b.ent("cut %s.%s" % (dst, leaves[0]))
    for stop in (tied, tied + 1, tied + 2, None):
        for root in (src, dst, keep):
            b.tot(root, stop)
            for leaf in leaves + ["v", "stale", "deep", "deep." + leaves[0], "deep." + leaves[2], "deep.fresh"]:
                b.ask("%s.%s" % (root, leaf), stop)
    return b.text()


def fam_tie_chain(rnd):
    """Ties of ties: moved operands compose, a write at any link shadows below it, and
    `old` in a shown definition reads the view its source already had."""
    b = Build()
    roots = rnd.sample(list(LETTERS), 4)
    ext = "ext"
    b.lay()
    b.ent("put %s lit %d" % (ext, rnd.randint(1, 9)))
    b.ent("put %s.k lit %d" % (roots[0], rnd.randint(1, 9)))
    b.lay()
    b.ent("put %s.v sum now %s.k old %s" % (roots[0], roots[0], ext))
    b.ent("put %s.w old %s.k" % (roots[0], roots[0]))
    b.ent("put %s lit %d" % (ext, rnd.randint(10, 19)))
    order = list(range(1, 4))
    rnd.shuffle(order)
    prev = roots[0]
    marks = []
    for i in order:
        b.lay()
        b.ent("tie %s %s" % (prev, roots[i]))
        marks.append(b.layers)
        if rnd.random() < 0.6:
            b.ent("put %s.k lit %d" % (roots[i], 10 * i + rnd.randint(1, 9)))
        prev = roots[i]
    b.lay()
    b.ent("put %s.k lit %d" % (roots[0], rnd.randint(50, 59)))
    b.ent("put %s lit %d" % (ext, rnd.randint(60, 69)))
    if rnd.random() < 0.5:
        b.ent("cut %s.k" % roots[order[0]])
    b.ent("put yes lit 1 if %s.v %d" % (roots[order[-1]], rnd.randint(1, 30)))
    b.ent("put no lit 2 un %s.w" % roots[order[-1]])
    for stop in marks + [None]:
        for r in roots:
            for leaf in ("k", "v", "w"):
                b.ask("%s.%s" % (r, leaf), stop)
            b.tot(r, stop)
    b.ask("yes")
    b.ask("no")
    return b.text()


def fam_tie_freeze(rnd):
    """A copy or a map taken over a tied region, and a tie placed under a copy: what is
    frozen, what stays live, and what a later write to either source moves."""
    b = Build()
    src, dst, cold, warm, other = rnd.sample(list(LETTERS), 5)
    b.lay()
    b.ent("put %s.a.k lit %d" % (src, rnd.randint(1, 9)))
    b.ent("put %s.a.v now %s.a.k" % (src, src))
    b.ent("put %s.b.k lit %d" % (src, rnd.randint(1, 9)))
    b.ent("put %s.k lit %d" % (other, rnd.randint(1, 9)))
    b.lay()
    b.ent("tie %s.a %s.a" % (src, dst))
    b.ent("put %s.b.k lit %d" % (dst, rnd.randint(10, 19)))
    frozen = b.lay()
    if rnd.random() < 0.5:
        b.ent("mix %s %s" % (dst, cold))
    else:
        b.ent("map %s %s" % (dst, cold))
    b.ent("tie %s %s.b.inner" % (other, cold))
    b.ent("map %s.a %s" % (dst, warm))
    b.lay()
    b.ent("put %s.a.k lit %d" % (src, rnd.randint(30, 39)))
    b.ent("put %s.k lit %d" % (other, rnd.randint(40, 49)))
    b.ent("put %s.a.x lit %d" % (src, rnd.randint(1, 9)))
    b.ent("put %s.k lit %d" % (warm, rnd.randint(70, 79)))
    b.lay()
    b.ent("tie %s %s.a" % (other, src))
    for stop in (frozen, frozen + 1, None):
        for r in (src, dst, cold):
            b.tot(r, stop)
            for leaf in ("a.k", "a.v", "a.x", "b.k", "b.inner.k"):
                b.ask("%s.%s" % (r, leaf), stop)
        b.ask("%s.k" % warm, stop)
        b.ask("%s.v" % warm, stop)
        b.tot(warm, stop)
    return b.text()


def fam_tie_ring(rnd):
    """Ties that lead back: mutual ties, a tie whose source lies under another tie, and a
    source deeper than its destination, counted and asked where the rules stop a lookup."""
    b = Build()
    a, c, d = rnd.sample(list(LETTERS), 3)
    b.lay()
    b.ent("put %s.x lit %d" % (a, rnd.randint(1, 9)))
    b.ent("put %s.y.z lit %d" % (c, rnd.randint(1, 9)))
    b.ent("put %s.q lit %d" % (d, rnd.randint(1, 9)))
    shape = rnd.randrange(3)
    b.lay()
    if shape == 0:
        b.ent("tie %s %s" % (a, c))
        b.ent("put %s.w lit %d" % (c, rnd.randint(1, 9)))
        b.lay()
        b.ent("tie %s %s" % (c, a))
    elif shape == 1:
        b.ent("tie %s %s" % (a, c))
        b.ent("tie %s.x %s.x" % (c, a))
        b.lay()
        b.ent("put %s.x.z lit %d" % (a, rnd.randint(1, 9)))
    else:
        b.ent("tie %s.y %s" % (a, c))
        b.ent("tie %s %s" % (c, a))
        b.lay()
        b.ent("put %s.y.y.x lit %d" % (a, rnd.randint(1, 9)))
    b.lay()
    b.ent("tie %s %s" % (rnd.choice((a, c)), d))
    b.ent("put %s.q lit %d if %s.x %d" % (d, rnd.randint(1, 9), c, rnd.randint(1, 9)))
    for stop in (1, 2, 3, None):
        for r in (a, c, d):
            b.tot(r, stop)
            for leaf in ("x", "y.z", "w", "q", "x.z", "y.y.x", "y.x", "x.x"):
                b.ask("%s.%s" % (r, leaf), stop)
    return b.text()


def fam_tie_interference(rnd):
    """Everything at once: ties, copies, maps, removals and guarded writes over three roots."""
    b = Build()
    roots = rnd.sample(list(LETTERS), 3)
    paths = [r + "." + leaf for r in roots for leaf in ("k", "v", "x")]
    paths += [r + ".d." + leaf for r in roots for leaf in ("k", "y")]
    b.lay()
    for p in paths:
        if rnd.random() < 0.8:
            b.ent("put %s lit %d" % (p, rnd.randint(-9, 9)))
    for _ in range(rnd.randint(4, 7)):
        b.lay()
        for _ in range(rnd.randint(2, 5)):
            roll = rnd.random()
            guard = None
            if rnd.random() < 0.2:
                watch = rnd.choice(paths)
                guard = ("un %s" % watch if rnd.random() < 0.5
                         else "if %s %d" % (watch, rnd.randint(-5, 5)))
            if roll < 0.35:
                b.ent("put %s %s" % (rnd.choice(paths), _expr(rnd, paths, 2)), guard)
            elif roll < 0.65:
                x, y = rnd.sample(roots, 2)
                if rnd.random() < 0.3:
                    y = y + ".d"
                b.ent("tie %s %s" % (x, y), guard)
            elif roll < 0.78:
                x, y = rnd.sample(roots, 2)
                b.ent("mix %s %s" % (x, y), guard)
            elif roll < 0.88:
                x, y = rnd.sample(roots, 2)
                b.ent("map %s %s" % (x, y), guard)
            else:
                b.ent("cut %s" % rnd.choice(paths), guard)
    for p in paths:
        b.ask(p)
        b.ask(p, rnd.randint(0, b.layers))
    _queries(b, rnd, paths, 10)
    for r in roots:
        b.tot(r)
        b.tot(r + ".d")
    return b.text()


def fam_tie_deep(rnd):
    """A tie's window copied back under its own source, again and again: every copy doubles
    what the tie shows, and sparse writes inside the copies must stay affordable."""
    b = Build()
    root = LETTERS[0]
    win = LETTERS[1]
    b.lay()
    b.ent("put %s.%s lit %d" % (root, LETTERS[25], rnd.randint(1, 9)))
    b.ent("put %s.%s.%s lit %d" % (root, LETTERS[24], LETTERS[23], rnd.randint(1, 9)))
    b.ent("put %s.o old %s.%s" % (root, root, LETTERS[25]))
    b.ent("tie %s %s" % (root, win))
    marks = []
    for i in range(21):
        b.lay()
        b.ent("mix %s %s.%s" % (win, root, LETTERS[i]))
        marks.append(b.layers)
        if i % 4 == 3:
            b.ent("put %s.%s.%s lit %d" % (root, LETTERS[i], LETTERS[25], 10 + i))
        if i % 5 == 4:
            b.ent("cut %s.%s.%s.%s" % (root, LETTERS[i], LETTERS[i - 1], LETTERS[25]))
    b.lay()
    b.ent("put %s.%s lit 37" % (root, LETTERS[25]))
    b.ent("put %s.f now %s.%s" % (win, win, LETTERS[25]))
    for stop in marks[::4] + [None]:
        b.tot(root, stop)
        b.tot(win, stop)
    for i in range(21):
        b.tot("%s.%s" % (root, LETTERS[i]))
        b.tot("%s.%s" % (win, LETTERS[i]))
    chain = win
    for i in range(6):
        chain = "%s.%s" % (chain, LETTERS[20 - i])
        b.ask("%s.%s" % (chain, LETTERS[25]))
        b.ask("%s.o" % chain)
        b.tot(chain)
    for _ in range(300):
        depth = rnd.randint(1, 16)
        segs = sorted(rnd.sample(list(LETTERS[:21]), depth), reverse=True)
        p = rnd.choice((root, win)) + "." + ".".join(segs)
        b.ask(p + "." + rnd.choice((LETTERS[25], "o", "f")))
        b.tot(p)
    return b.text()


FAMS = FAMS + (("mapcapture", fam_map_capture), ("mapedit", fam_map_edit),
               ("mapinterference", fam_map_interference), ("mapoverlap", fam_map_overlap),
               ("tielive", fam_tie_live), ("tiechain", fam_tie_chain),
               ("tiefreeze", fam_tie_freeze), ("tiering", fam_tie_ring),
               ("tieinterference", fam_tie_interference))

SCALE = (("wide", fam_wide), ("deep", fam_deep), ("mapdeep", fam_map_deep),
         ("tiedeep", fam_tie_deep))


def fam_veil_live(rnd):
    b = Build()
    s, d = rnd.sample(list(LETTERS), 2)
    x, y, z = rnd.sample(list(LETTERS), 3)
    b.lay()
    b.ent("put %s.%s lit %d" % (s, x, rnd.randint(1, 9)))
    b.ent("put %s.%s lit %d" % (d, x, rnd.randint(10, 19)))
    b.ent("put %s.%s lit %d" % (d, y, rnd.randint(20, 29)))
    b.lay()
    b.ent("veil %s %s" % (s, d))
    b.ent("put %s.%s now %s.%s" % (s, z, s, x))
    b.lay()
    b.ent("put %s.%s lit %d" % (s, x, rnd.randint(30, 39)))
    if rnd.random() < 0.5:
        b.ent("put %s.%s lit %d" % (s, y, rnd.randint(40, 49)))
    for stop in (1, 2, 3, None):
        for leaf in (x, y, z):
            b.ask("%s.%s" % (d, leaf), stop)
        b.tot(d, stop)
    return b.text()


def fam_veil_mask(rnd):
    b = Build()
    s, d, c = rnd.sample(list(LETTERS), 3)
    x, y, z = rnd.sample(list(LETTERS), 3)
    b.lay()
    for root, val in ((s, 1), (d, 10)):
        for leaf in (x, y):
            b.ent("put %s.%s.%s lit %d" % (root, c, leaf, val + rnd.randint(1, 9)))
    b.ent("put %s.%s lit 3" % (d, z))
    b.ent("veil %s %s" % (s, d))
    b.lay()
    b.ent("cut %s.%s" % (d, c))
    b.ent("put %s.%s.%s lit %d" % (d, c, x, rnd.randint(30, 39)))
    b.ent("put %s.%s lit %d" % (s, z, rnd.randint(40, 49)))
    for stop in (1, 2, None):
        for leaf in (x, y):
            b.ask("%s.%s.%s" % (d, c, leaf), stop)
        b.ask("%s.%s" % (d, z), stop)
        b.tot(d, stop)
    return b.text()


def fam_veil_copy(rnd):
    b = Build()
    s, d, m, n = rnd.sample(list(LETTERS), 4)
    k, v = rnd.sample(list(LETTERS), 2)
    b.lay()
    b.ent("put %s.%s lit %d" % (s, k, rnd.randint(1, 9)))
    b.ent("put %s.%s now %s.%s" % (s, v, s, k))
    b.ent("put %s.%s lit %d" % (d, k, rnd.randint(10, 19)))
    b.ent("veil %s %s" % (s, d))
    b.lay()
    b.ent("mix %s %s" % (d, m))
    b.ent("map %s %s" % (d, n))
    b.lay()
    b.ent("put %s.%s lit %d" % (s, k, rnd.randint(20, 29)))
    b.ent("put %s.%s lit %d" % (d, k, rnd.randint(30, 39)))
    for stop in (1, 2, None):
        for root in (s, d, m, n):
            b.ask("%s.%s" % (root, k), stop)
            b.ask("%s.%s" % (root, v), stop)
            b.tot(root, stop)
    return b.text()


def fam_veil_chain(rnd):
    b = Build()
    s, d, e, f = rnd.sample(list(LETTERS), 4)
    k, v = rnd.sample(list(LETTERS), 2)
    b.lay()
    b.ent("put %s.%s lit %d" % (s, k, rnd.randint(1, 9)))
    b.ent("put %s.%s now %s.%s" % (s, v, s, k))
    b.ent("put %s.%s lit %d" % (d, k, rnd.randint(10, 19)))
    b.ent("put %s.%s lit %d" % (e, v, rnd.randint(20, 29)))
    b.ent("veil %s %s" % (s, d))
    b.ent("veil %s %s" % (d, e))
    b.ent("tie %s %s" % (e, f))
    b.lay()
    b.ent("put %s.%s lit %d" % (s, k, rnd.randint(30, 39)))
    if rnd.random() < 0.5:
        b.ent("cut %s.%s" % (d, v))
    for stop in (1, 2, None):
        for root in (s, d, e, f):
            b.ask("%s.%s" % (root, v), stop)
            b.tot(root, stop)
    return b.text()


def fam_veil_old(rnd):
    b = Build()
    s, d = rnd.sample(list(LETTERS), 2)
    k, v = rnd.sample(list(LETTERS), 2)
    b.lay()
    b.ent("put %s.%s lit %d" % (d, k, rnd.randint(1, 9)))
    b.lay()
    b.ent("put %s.%s sum old %s.%s lit 1" % (d, v, d, k))
    b.ent("put %s.%s lit %d" % (s, k, rnd.randint(10, 19)))
    b.ent("put %s.%s sum now %s.%s old %s.%s" % (s, v, s, k, s, k))
    b.ent("veil %s %s" % (s, d))
    b.lay()
    b.ent("cut %s.%s" % (s, v))
    b.ent("put %s.%s lit %d" % (s, k, rnd.randint(20, 29)))
    for stop in (1, 2, 3, None):
        for root in (s, d):
            b.ask("%s.%s" % (root, k), stop)
            b.ask("%s.%s" % (root, v), stop)
            b.tot(root, stop)
    return b.text()


def fam_veil_deep(rnd):
    b = Build()
    s, d = "a", "b"
    b.lay()
    b.ent("put %s.z lit %d" % (s, rnd.randint(1, 9)))
    b.ent("put %s.y.x lit %d" % (s, rnd.randint(10, 19)))
    marks = []
    for i in range(21):
        b.lay()
        b.ent("mix %s %s.%s" % (s, s, LETTERS[i]))
        marks.append(b.layers)
    b.lay()
    b.ent("mix %s %s" % (s, d))
    b.ent("veil %s %s" % (s, d))
    before = b.layers
    b.lay()
    b.ent("put %s.%s.z lit %d" % (s, LETTERS[0], rnd.randint(20, 29)))
    b.ent("cut %s.%s.y" % (d, LETTERS[1]))
    b.ent("put %s.new lit %d" % (d, rnd.randint(30, 39)))
    for stop in (marks[8], marks[-1], before, None):
        b.tot(s, stop)
        b.tot(d, stop)
    for i in range(4):
        b.ask("%s.%s.z" % (d, LETTERS[i]))
        b.tot("%s.%s" % (d, LETTERS[i]))
    return b.text()


def fam_veil_random(rnd):
    b = Build()
    roots = rnd.sample(list(LETTERS), 4)
    leaves = rnd.sample(list(LETTERS), 4)
    paths = [r + "." + leaf for r in roots for leaf in leaves[:3]]
    paths += [r + "." + leaves[3] + "." + leaf for r in roots for leaf in leaves[:2]]
    b.lay()
    for _ in range(5):
        b.ent("put %s %s" % (rnd.choice(paths), _expr(rnd, paths, 2)))
    a, d = rnd.sample(roots, 2)
    b.ent("veil %s %s" % (a, d))
    for _ in range(4):
        b.lay()
        for _ in range(rnd.randint(1, 3)):
            roll = rnd.random()
            if roll < 0.40:
                b.ent("put %s %s" % (rnd.choice(paths), _expr(rnd, paths, 2)))
            elif roll < 0.58:
                b.ent("cut %s" % rnd.choice(paths))
            else:
                src, dst = rnd.sample(roots, 2)
                op = rnd.choice(("mix", "map"))
                b.ent("%s %s %s" % (op, src, dst))
    for _ in range(12):
        p = rnd.choice(paths)
        b.ask(p, rnd.randint(0, b.layers))
    for r in roots:
        b.tot(r)
        b.tot(r, rnd.randint(0, b.layers))
    return b.text()


FAMS = FAMS + (("veillive", fam_veil_live), ("veilmask", fam_veil_mask),
               ("veilcopy", fam_veil_copy), ("veilchain", fam_veil_chain),
               ("veilold", fam_veil_old), ("veilrandom", fam_veil_random))
SCALE = SCALE + (("veildeep", fam_veil_deep),)


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
