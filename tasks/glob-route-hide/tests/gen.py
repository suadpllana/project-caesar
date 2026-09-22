"""Programs generated from a seed drawn after the agent's container is gone.

The families are shaped around the rules rather than sampled uniformly: a uniform population is
mostly public lines in acyclic imports, where every wrong reading of visibility, hiding and
cycles prints the same lines as the right one. Each small family concentrates one mechanism;
the two scale families exist for the execution limit rather than for a rule.

  plain    acyclic public imports, one module tree or several: the everyday case
  nest     modules reading their parents and children, private items and private globs
  narrow   chains of re-exports with private hops, public detours, readers inside and out
  hide     modules whose own lines bind a name their public globs also offer
  broken   own imports that find nothing, and own lines gated on and off
  ring     cycles of globs fed from outside, with members binding a name that flows round
  amb      one name from several sources, carried through re-exports, filtered by readers
  rename   renames, chains of renames and renames onto names the globs offer
  gate     flags deciding which globs, own lines and items are present
  mix      everything at random, small
  tree     about four thousand modules, each reading its parent and re-exporting its children
  mesh     about three thousand flat modules reading each other through globs at random

Every program is a list of lines without newlines; `programs(seed, per)` returns
(family, name, lines) for every family, `per` programs of each small family and BIG of each
scale family.
"""
import random

FAMILIES = (
    ("plain", False),
    ("nest", False),
    ("narrow", False),
    ("hide", False),
    ("broken", False),
    ("ring", False),
    ("amb", False),
    ("rename", False),
    ("gate", False),
    ("mix", False),
    ("tree", True),
    ("mesh", True),
)

BIG = 3
POOL = ("f", "g", "h", "k", "n", "p", "q", "r", "s", "w")
FLAGS = ("dbg", "fast", "lite")


class Prog:
    """A program under construction: modules in file order, each with its lines."""

    def __init__(self, rng, flags=()):
        self.rng = rng
        self.flags = list(flags)
        self.order = []
        self.body = {}

    def mod(self, path):
        if path not in self.body:
            self.order.append(path)
            self.body[path] = []
        return path

    def put(self, path, text):
        self.body[path].append(text)

    def lines(self):
        out = ["flags" + "".join(" " + f for f in self.flags)]
        for m in self.order:
            out.append("mod " + m)
            out.extend(self.body[m])
        return out


def _pub(rng, p):
    return "pub " if rng.random() < p else ""


def _cond(rng, p):
    if rng.random() >= p:
        return ""
    return " if " + ("!" if rng.random() < 0.5 else "") + rng.choice(FLAGS)


def _forest(rng, tops, kids, depth):
    """Module paths of a small forest, parents before children."""
    out = []
    names = ["a", "ab", "b", "c", "cd", "u", "uv", "x", "y", "z"]
    rng.shuffle(names)
    if rng.random() < 0.5:
        names = sorted(names[:tops], key=len) + names[tops:]
    for t in names[:tops]:
        stack = [(t, 1)]
        while stack:
            p, d = stack.pop(0)
            out.append(p)
            if d < depth:
                for j in range(rng.randint(*kids)):
                    stack.append(("%s.%s" % (p, "mnopq"[j]), d + 1))
    return out


def _refs(prog, rng, mods, names, lo, hi):
    for m in mods:
        for _ in range(rng.randint(lo, hi)):
            prog.put(m, "ref " + rng.choice(names))


# --- small families ------------------------------------------------------------------------

def plain(rng):
    p = Prog(rng)
    mods = _forest(rng, rng.randint(2, 4), (0, 2), 3)
    for m in mods:
        p.mod(m)
    names = list(POOL[:rng.randint(3, 6)])
    for m in mods:
        for _ in range(rng.randint(0, 2)):
            p.put(m, "%sitem %s" % (_pub(rng, 0.85), rng.choice(names)))
    order = list(mods)
    rng.shuffle(order)
    for i, m in enumerate(order):
        later = order[i + 1:]
        for src in rng.sample(later, min(len(later), rng.randint(0, 3))):
            p.put(m, "%suse %s::*" % (_pub(rng, 0.7), src))
    _refs(p, rng, mods, names, 1, 3)
    return p.lines()


def nest(rng):
    p = Prog(rng)
    mods = _forest(rng, rng.randint(1, 3), (1, 3), rng.randint(3, 4))
    for m in mods:
        p.mod(m)
    names = list(POOL[:rng.randint(3, 6)])
    for m in mods:
        for _ in range(rng.randint(0, 2)):
            p.put(m, "%sitem %s" % (_pub(rng, 0.45), rng.choice(names)))
    for m in mods:
        par = m.rpartition(".")[0]
        if par and rng.random() < 0.75:
            p.put(m, "%suse %s::*" % (_pub(rng, 0.3), par))
        gp = par.rpartition(".")[0] if par else ""
        if gp and rng.random() < 0.25:
            p.put(m, "%suse %s::*" % (_pub(rng, 0.3), gp))
        for c in [x for x in mods if x.rpartition(".")[0] == m]:
            if rng.random() < 0.45:
                p.put(m, "%suse %s::*" % (_pub(rng, 0.6), c))
        if rng.random() < 0.3:
            other = rng.choice(mods)
            if other != m:
                p.put(m, "%suse %s::%s" % (_pub(rng, 0.5), other, rng.choice(names)))
    sibs = []
    if rng.random() < 0.6:
        top = rng.choice([m for m in mods if "." not in m])
        sib = p.mod(top + "q")
        sibs.append(sib)
        p.put(sib, "%suse %s::*" % (_pub(rng, 0.3), top))
        if rng.random() < 0.5:
            p.put(sib, "use %s::%s" % (top, rng.choice(names)))
    _refs(p, rng, mods + sibs, names, 1, 3)
    return p.lines()


def narrow(rng):
    p = Prog(rng)
    tops = ["a", "b", "c", "d"]
    rng.shuffle(tops)
    src = p.mod(tops[0])
    names = list(POOL[:rng.randint(2, 4)])
    for n in names:
        p.put(src, "%sitem %s" % (_pub(rng, 0.8), n))
    hub = tops[1]
    chain = [p.mod(hub)]
    for j in range(rng.randint(1, 3)):
        chain.append(p.mod("%s.%s" % (chain[-1], "mnopq"[j])))
    readers = [p.mod(tops[2]), p.mod(tops[3])]
    readers.append(p.mod("%s.%s" % (tops[2], "x")))
    inner = [p.mod("%s.%s" % (m, "y")) for m in chain[:2]]
    # the chain passes the source down and back, some hops private
    last = src
    for m in chain:
        p.put(m, "%suse %s::*" % (_pub(rng, 0.5), last))
        last = m
    # public detours and cycles that can widen what a private hop narrowed
    for m in chain:
        if rng.random() < 0.45:
            p.put(m, "pub use %s::*" % rng.choice(chain + [src]))
    if rng.random() < 0.6:
        p.put(chain[0], "pub use %s::*" % chain[-1])
    for m in chain:
        if rng.random() < 0.5:
            via = p.mod("%s.w" % m)
            p.put(m, "use %s::*" % src)
            p.put(m, "pub use %s::*" % via)
            p.put(via, "pub use %s::*" % rng.choice([src, chain[0]]))
            if rng.random() < 0.5:
                p.put(via, "pub use %s::*" % m)
    for r in readers + inner:
        for _ in range(rng.randint(1, 2)):
            p.put(r, "%suse %s::*" % (_pub(rng, 0.5), rng.choice(chain + readers + inner)))
        if rng.random() < 0.3:
            p.put(r, "%suse %s::%s" % (_pub(rng, 0.5), rng.choice(chain), rng.choice(names)))
    _refs(p, rng, chain + readers + inner, names, 1, 3)
    return p.lines()


def hide(rng):
    p = Prog(rng)
    tops = ["a", "b", "c", "d", "e", "u"]
    rng.shuffle(tops)
    names = list(POOL[:rng.randint(2, 4)])
    s1, s2 = p.mod(tops[0]), p.mod(tops[1])
    for n in names:
        p.put(s1, "pub item %s" % n)
        if rng.random() < 0.6:
            p.put(s2, "%sitem %s" % (_pub(rng, 0.8), n))
    hider = p.mod(tops[2])
    kid = p.mod(hider + ".k")
    p.put(hider, "pub use %s::*" % s1)
    for n in names:
        r = rng.random()
        if r < 0.25:
            p.put(hider, "item %s" % n)
        elif r < 0.45:
            p.put(hider, "use %s::%s" % (s2, n))
        elif r < 0.6:
            p.put(hider, "pub use %s::%s" % (s2, n))
        elif r < 0.7:
            p.put(hider, "use %s::%s" % (tops[5], n))
    p.put(kid, "%suse %s::*" % (_pub(rng, 0.4), hider))
    out1, out2 = p.mod(tops[3]), p.mod(tops[4])
    p.put(out1, "use %s::*" % hider)
    p.put(out2, "use %s::*" % kid)
    if rng.random() < 0.5:
        p.put(out2, "use %s::*" % s2)
    if rng.random() < 0.4:
        p.put(out1, "%suse %s::%s" % (_pub(rng, 0.5), hider, rng.choice(names)))
    _refs(p, rng, [hider, kid, out1, out2], names, 1, 3)
    return p.lines()


def broken(rng):
    p = Prog(rng, [f for f in FLAGS if rng.random() < 0.5])
    tops = ["a", "b", "c", "d", "e"]
    rng.shuffle(tops)
    names = list(POOL[:rng.randint(2, 4)])
    s = p.mod(tops[0])
    priv = p.mod(tops[1] + ".z")
    for n in names:
        p.put(s, "%sitem %s" % (_pub(rng, 0.85), n))
        p.put(priv, "item %s" % n)
    mods = [p.mod(tops[2]), p.mod(tops[3]), p.mod(tops[2] + ".w")]
    for m in mods:
        p.put(m, "%suse %s::*" % (_pub(rng, 0.5), s))
        for n in names:
            r = rng.random()
            src = rng.choice([s, priv, tops[4], tops[1]])
            if r < 0.5:
                p.put(m, "%suse %s::%s%s" % (_pub(rng, 0.4), src, rng.choice(names + ["zz"]),
                                              _cond(rng, 0.5)))
            elif r < 0.65:
                p.put(m, "%suse %s::%s as %s%s" % (_pub(rng, 0.4), src, rng.choice(names), n,
                                                    _cond(rng, 0.5)))
            elif r < 0.8:
                p.put(m, "item %s%s" % (n, _cond(rng, 0.7)))
    reader = p.mod(tops[4])
    p.put(reader, "use %s::*" % rng.choice(mods))
    _refs(p, rng, mods + [reader], names, 1, 3)
    return p.lines()


def ring(rng):
    p = Prog(rng)
    n_ring = rng.randint(3, 7)
    ring_mods = ["r%d" % i for i in range(n_ring)]
    if rng.random() < 0.4:
        ring_mods = ["h." + m for m in ring_mods]
        p.mod("h")
    for m in ring_mods:
        p.mod(m)
    names = list(POOL[:rng.randint(2, 4)])
    feeds = [p.mod("s%d" % i) for i in range(rng.randint(1, 3))]
    for f in feeds:
        for n in rng.sample(names, rng.randint(1, len(names))):
            p.put(f, "%sitem %s" % (_pub(rng, 0.85), n))
    for i, m in enumerate(ring_mods):
        p.put(m, "%suse %s::*" % (_pub(rng, 0.85), ring_mods[(i + 1) % n_ring]))
        if rng.random() < 0.3:
            p.put(m, "%suse %s::*" % (_pub(rng, 0.7), rng.choice(ring_mods)))
    for f in feeds:
        p.put(rng.choice(ring_mods), "%suse %s::*" % (_pub(rng, 0.7), f))
    for m in ring_mods:
        r = rng.random()
        if r < 0.3:
            p.put(m, "%sitem %s" % (_pub(rng, 0.7), rng.choice(names)))
        elif r < 0.45:
            p.put(m, "%suse %s::%s" % (_pub(rng, 0.6), rng.choice(feeds), rng.choice(names)))
    readers = [p.mod("o%d" % i) for i in range(rng.randint(1, 2))]
    for o in readers:
        p.put(o, "%suse %s::*" % (_pub(rng, 0.5), rng.choice(ring_mods)))
    _refs(p, rng, ring_mods + readers, names, 1, 2)
    return p.lines()


def amb(rng):
    p = Prog(rng)
    tops = ["a", "b", "c", "d", "e", "u", "v", "x"]
    rng.shuffle(tops)
    names = list(POOL[:rng.randint(1, 3)])
    # sources are declared in an order unrelated to the order readers reach them
    srcs = [p.mod(tops[i]) for i in range(rng.randint(2, 4))]
    nested = p.mod(srcs[0] + ".in")
    for s in srcs + [nested]:
        for n in names:
            if rng.random() < 0.75:
                p.put(s, "%sitem %s" % (_pub(rng, 0.75), n))
    mids = [p.mod(tops[5]), p.mod(tops[6])]
    for m in mids:
        for s in rng.sample(srcs, rng.randint(1, len(srcs))):
            p.put(m, "%suse %s::*" % (_pub(rng, 0.7), s))
        if rng.random() < 0.4:
            p.put(m, "pub use %s::*" % nested)
    top = p.mod(tops[7])
    for m in mids:
        p.put(top, "%suse %s::*" % (_pub(rng, 0.6), m))
    if rng.random() < 0.6:
        n = rng.choice(names)
        p.put(top, "%suse %s::%s%s" % (_pub(rng, 0.5), rng.choice(mids), n,
                                        " as %s" % rng.choice(names) if rng.random() < 0.3 else ""))
    if rng.random() < 0.5:
        p.put(top, "use %s::*" % rng.choice(srcs))
    inner = p.mod(srcs[0] + ".in.deep")
    p.put(inner, "use %s::*" % rng.choice(mids))
    p.put(inner, "use %s::*" % nested)
    if rng.random() < 0.5:
        p.put(inner, "%suse %s::%s" % (_pub(rng, 0.5), rng.choice(mids), rng.choice(names)))
    _refs(p, rng, mids + [top, inner, nested], names, 1, 2)
    return p.lines()


def rename(rng):
    p = Prog(rng)
    mods = _forest(rng, rng.randint(3, 5), (0, 1), 2)
    for m in mods:
        p.mod(m)
    names = list(POOL[:rng.randint(3, 5)])
    for m in mods:
        if rng.random() < 0.6:
            p.put(m, "%sitem %s" % (_pub(rng, 0.8), rng.choice(names)))
    for m in mods:
        for _ in range(rng.randint(1, 3)):
            src = rng.choice(mods)
            r = rng.random()
            if r < 0.55:
                p.put(m, "%suse %s::%s as %s" % (_pub(rng, 0.7), src, rng.choice(names),
                                                  rng.choice(names)))
            elif r < 0.75:
                p.put(m, "%suse %s::%s" % (_pub(rng, 0.7), src, rng.choice(names)))
            else:
                p.put(m, "%suse %s::*" % (_pub(rng, 0.7), src))
    _refs(p, rng, mods, names, 1, 3)
    return p.lines()


def gate(rng):
    p = Prog(rng, [f for f in FLAGS if rng.random() < 0.5])
    mods = _forest(rng, rng.randint(3, 5), (0, 1), 2)
    for m in mods:
        p.mod(m)
    names = list(POOL[:rng.randint(2, 4)])
    for m in mods:
        for _ in range(rng.randint(0, 2)):
            p.put(m, "%sitem %s%s" % (_pub(rng, 0.75), rng.choice(names), _cond(rng, 0.5)))
    for m in mods:
        for _ in range(rng.randint(1, 3)):
            src = rng.choice(mods)
            if rng.random() < 0.65:
                p.put(m, "%suse %s::*%s" % (_pub(rng, 0.7), src, _cond(rng, 0.6)))
            else:
                p.put(m, "%suse %s::%s%s" % (_pub(rng, 0.6), src, rng.choice(names),
                                              _cond(rng, 0.7)))
    _refs(p, rng, mods, names, 1, 3)
    return p.lines()


def mix(rng):
    p = Prog(rng, [f for f in FLAGS if rng.random() < 0.5])
    mods = _forest(rng, rng.randint(2, 4), (0, 2), 3)
    for m in mods:
        p.mod(m)
    names = list(POOL[:rng.randint(3, 6)])
    for m in mods:
        for _ in range(rng.randint(0, 4)):
            r = rng.random()
            pub = _pub(rng, 0.55)
            c = _cond(rng, 0.2)
            if r < 0.3:
                p.put(m, "%sitem %s%s" % (pub, rng.choice(names), c))
            elif r < 0.55:
                src = rng.choice(mods + ["zz"]) if rng.random() < 0.9 else "zz"
                if rng.random() < 0.3:
                    p.put(m, "%suse %s::%s as %s%s" % (pub, src, rng.choice(names),
                                                        rng.choice(names), c))
                else:
                    p.put(m, "%suse %s::%s%s" % (pub, src, rng.choice(names), c))
            else:
                p.put(m, "%suse %s::*%s" % (pub, rng.choice(mods), c))
    _refs(p, rng, mods, names, 0, 3)
    return p.lines()


# --- scale families -------------------------------------------------------------------------

def tree(rng, size=4000):
    """Every module reads its parent through a private glob and re-exports each child.

    The whole tree is one cycle of globs and every module ends up holding every name. Names
    declared in two modules are cut by each other; private items reach only their subtree;
    a few modules bind a flowing name themselves.
    """
    p = Prog(rng)
    root = p.mod("t")
    kids = {root: []}
    queue = [root]
    qi = 0
    count = 1
    while count < size:
        par = queue[qi]
        qi += 1
        for _ in range(rng.randint(2, 4)):
            if count >= size:
                break
            c = "%s.m%d" % (par, len(kids[par]))
            kids[par].append(c)
            kids[c] = []
            queue.append(c)
            count += 1
    names = []
    decl = {}
    k = 0
    for m in queue:
        lst = []
        for _ in range(rng.randint(2, 4)):
            lst.append(("v%d" % k, rng.random() >= 0.06))
            names.append("v%d" % k)
            k += 1
        decl[m] = lst
    for m in queue:
        if rng.random() < 0.03:
            decl[m].append((rng.choice(names), True))
    for m in queue:
        p.mod(m)
        par = m.rpartition(".")[0]
        if par:
            p.put(m, "use %s::*" % par)
        for c in kids[m]:
            p.put(m, "pub use %s::*" % c)
        for n, pub in decl[m]:
            p.put(m, ("pub item %s" if pub else "item %s") % n)
        if rng.random() < 0.01:
            p.put(m, "use %s::%s" % (rng.choice(queue), rng.choice(names)))
        for _ in range(rng.randint(1, 2)):
            p.put(m, "ref " + rng.choice(names))
    return p.lines()


def mesh(rng, size=3000):
    """Flat modules reading each other through globs at random: one large strongly connected set.

    Private globs narrow what they pass to the reading module alone, a few modules bind a name
    they also read, a few names are declared twice, and a few items are private.
    """
    p = Prog(rng)
    mods = ["w%d" % i for i in range(size)]
    for m in mods:
        p.mod(m)
    names = []
    k = 0
    for m in mods:
        for _ in range(rng.randint(2, 3)):
            n = "v%d" % k
            k += 1
            names.append(n)
            p.put(m, "%sitem %s" % ("pub " if rng.random() >= 0.05 else "", n))
    for m in mods:
        if rng.random() < 0.03:
            p.put(m, "pub item %s" % rng.choice(names))
        for src in rng.sample(mods, rng.randint(1, 3)):
            if src != m:
                p.put(m, "%suse %s::*" % ("pub " if rng.random() >= 0.08 else "", src))
        if rng.random() < 0.02:
            p.put(m, "%suse %s::%s" % (_pub(rng, 0.5), rng.choice(mods), rng.choice(names)))
        for _ in range(rng.randint(1, 2)):
            p.put(m, "ref " + rng.choice(names))
    return p.lines()


SMALL = {
    "plain": plain, "nest": nest, "narrow": narrow, "hide": hide, "broken": broken,
    "ring": ring, "amb": amb, "rename": rename, "gate": gate, "mix": mix,
}
LARGE = {"tree": tree, "mesh": mesh}


def programs(seed, per):
    out = []
    for fam, big in FAMILIES:
        count = BIG if big else per
        fn = LARGE[fam] if big else SMALL[fam]
        for i in range(count):
            rng = random.Random("%s:%s:%d" % (seed, fam, i))
            out.append((fam, "%s-%02d" % (fam, i), fn(rng)))
    return out
