"""The generated population, drawn from a seed the submission never sees.

Eleven families. Nine are small and concentrate one mechanism each far above the rate a
random program would reach: writes that land where they stand, a device with no room to
spare so a write has to live on the blocks it frees, a free map cut into runs so one
allocation is spread over several, stamping and dropping so exclusivity moves, ranges
shared until several claims stand on one block, defragmenting shared and unshared items,
sets of lines for the freed-by-dropping question, and stamp trees that lose lines and share
across families for the family questions. Three are large and exist for the execution limit
rather than for a rule: `wide` asks for charges thousands of times against a line standing
on thousands of spans, `churn` allocates against a free map cut into thousands of runs, and
`tree` asks the family questions thousands of times of a stamp tree of two hundred lines
that keeps losing some of them.

A census of unshaped programs put the room check at 1 per cent of programs and an
allocation spread over runs at 3; the families below put each of them in a family of
its own.
"""
import random

FAMILIES = (
    ("plain", True),
    ("place", True),
    ("tight", True),
    ("frag", True),
    ("stampy", True),
    ("weave", True),
    ("vacuum", True),
    ("sets", True),
    ("fam", True),
    ("wide", False),
    ("churn", False),
    ("tree", False),
)

BIG = 3

# The tree family's shape, measured in authoring/span-claim-charge/time_tree.py.
TREE_STAMPS = 240
TREE_WRITES = 40
TREE_ASKS = 250
TREE_ITEMS = (810, 900, 990)

LINES = "abcdefgh"
ITEMS = "fghijklm"


def _plain(rng):
    blocks = rng.choice([48, 64, 96, 160, 256])
    rows = ["dev %d" % blocks]
    live = ["a"]
    kit = {"a": []}
    rows.append("n a")
    for _ in range(rng.randint(20, 55)):
        pick = rng.random()
        ln = rng.choice(live)
        if pick < 0.07:
            name = rng.choice(LINES)
            rows.append("n %s" % name)
            if name not in live:
                live.append(name)
                kit[name] = []
        elif pick < 0.15 and kit[ln]:
            dst = rng.choice(LINES)
            rows.append("p %s %s" % (ln, dst))
            if dst not in live:
                live.append(dst)
                kit[dst] = list(kit[ln])
        elif pick < 0.19 and len(live) > 1:
            rows.append("d %s" % ln)
            live.remove(ln)
            kit.pop(ln, None)
        elif pick < 0.52:
            nm = rng.choice(ITEMS)
            rows.append("w %s/%s %d %d" % (ln, nm, rng.randint(0, 10), rng.randint(1, 12)))
            if nm not in kit[ln]:
                kit[ln].append(nm)
        elif pick < 0.64 and kit[ln]:
            dl = rng.choice(live)
            dn = rng.choice(ITEMS)
            rows.append("s %s/%s %d %d %s/%s %d" % (
                ln, rng.choice(kit[ln]), rng.randint(0, 6), rng.randint(1, 6),
                dl, dn, rng.randint(0, 6)))
            if dn not in kit[dl]:
                kit[dl].append(dn)
        elif pick < 0.70 and kit[ln]:
            rows.append("t %s/%s %d" % (ln, rng.choice(kit[ln]), rng.randint(0, 10)))
        elif pick < 0.75 and kit[ln]:
            nm = rng.choice(kit[ln])
            rows.append("x %s/%s" % (ln, nm))
            kit[ln].remove(nm)
        elif pick < 0.80 and kit[ln]:
            rows.append("v %s/%s" % (ln, rng.choice(kit[ln])))
        elif pick < 0.87:
            rows.append("c %s" % ln)
        elif pick < 0.91:
            k = rng.randint(1, min(3, len(live)))
            rows.append("g %s" % ",".join(rng.sample(sorted(live), k)))
        elif pick < 0.96 and kit[ln]:
            rows.append("m %s/%s" % (ln, rng.choice(kit[ln])))
        else:
            rows.append("f")
    return rows


def _place(rng):
    """Overwrites that mostly land where they stand, broken by the odd share."""
    blocks = rng.choice([96, 128, 192])
    rows = ["dev %d" % blocks, "n a"]
    names = ITEMS[:rng.randint(3, 5)]
    sizes = {}
    for nm in names:
        wide = rng.randint(8, 20)
        rows.append("w a/%s 0 %d" % (nm, wide))
        sizes[nm] = wide
    for _ in range(rng.randint(18, 40)):
        nm = rng.choice(names)
        pick = rng.random()
        if pick < 0.62:
            at = rng.randint(0, sizes[nm])
            n = rng.randint(1, max(1, sizes[nm] - at) if at < sizes[nm] else 4)
            rows.append("w a/%s %d %d" % (nm, at, n))
            sizes[nm] = max(sizes[nm], at + n)
        elif pick < 0.78:
            src = rng.choice(names)
            n = rng.randint(1, max(1, min(4, sizes[src])))
            at = rng.randint(0, sizes[src] - n)
            to = rng.randint(0, sizes[nm])
            rows.append("s a/%s %d %d a/%s %d" % (src, at, n, nm, to))
            sizes[nm] = max(sizes[nm], to + n)
        elif pick < 0.88:
            rows.append("m a/%s" % nm)
        elif pick < 0.95:
            rows.append("f")
        else:
            rows.append("c a")
    rows.append("c a")
    rows.append("f")
    return rows


def _tight(rng):
    """A device with nothing to spare, so a write lives on what it frees."""
    blocks = rng.choice([16, 20, 24, 28, 32])
    rows = ["dev %d" % blocks, "n a"]
    left = blocks
    names = []
    while left > 0 and len(names) < 5:
        wide = min(left, rng.randint(2, 8))
        nm = ITEMS[len(names)]
        rows.append("w a/%s 0 %d" % (nm, wide))
        names.append((nm, wide))
        left -= wide
    for _ in range(rng.randint(14, 30)):
        nm, wide = rng.choice(names)
        pick = rng.random()
        if pick < 0.34:
            rows.append("w a/%s 0 %d" % (nm, wide))
        elif pick < 0.5:
            at = rng.randint(0, max(0, wide - 1))
            rows.append("w a/%s %d %d" % (nm, at, rng.randint(1, wide)))
        elif pick < 0.62 and wide >= 2:
            half = wide // 2
            rows.append("s a/%s 0 %d a/%s %d" % (nm, half, nm, wide - half))
        elif pick < 0.72:
            rows.append("x a/%s" % nm)
        elif pick < 0.8:
            rows.append("v a/%s" % nm)
        elif pick < 0.9:
            rows.append("f")
        else:
            rows.append("c a")
    rows.append("f")
    rows.append("c a")
    return rows


def _frag(rng):
    """Many runs, then writes too large for any one of them."""
    blocks = rng.choice([64, 96, 128, 160])
    rows = ["dev %d" % blocks, "n a"]
    unit = rng.choice([2, 3, 4])
    count = min(blocks // unit, rng.randint(8, 16))
    for k in range(count):
        rows.append("w a/i%d 0 %d" % (k, unit))
    keep = set(rng.sample(range(count), count // 2))
    for k in range(count):
        if k not in keep:
            rows.append("x a/i%d" % k)
    rows.append("f")
    for _ in range(rng.randint(4, 9)):
        want = rng.randint(unit + 1, unit * rng.randint(3, 6))
        nm = rng.choice(ITEMS)
        rows.append("w a/%s 0 %d" % (nm, want))
        rows.append("m a/%s" % nm)
        rows.append("f")
        if rng.random() < 0.4:
            rows.append("x a/%s" % nm)
    rows.append("c a")
    return rows


def _stampy(rng):
    """Stamps, divergent writes, and drops, with the charges watched throughout."""
    blocks = rng.choice([96, 128, 256])
    rows = ["dev %d" % blocks, "n a"]
    names = ITEMS[:rng.randint(2, 4)]
    sizes = {}
    for nm in names:
        wide = rng.randint(4, 12)
        rows.append("w a/%s 0 %d" % (nm, wide))
        sizes[nm] = wide
    live = ["a"]
    for _ in range(rng.randint(16, 34)):
        pick = rng.random()
        ln = rng.choice(live)
        if pick < 0.2 and len(live) < 5:
            dst = LINES[len(live)]
            rows.append("p %s %s" % (ln, dst))
            live.append(dst)
            rows.append("c %s" % ln)
            rows.append("c %s" % dst)
        elif pick < 0.3 and len(live) > 1:
            gone = rng.choice(live[1:])
            rows.append("d %s" % gone)
            live.remove(gone)
            rows.append("f")
        elif pick < 0.72:
            nm = rng.choice(names)
            at = rng.randint(0, sizes[nm])
            rows.append("w %s/%s %d %d" % (ln, nm, at, rng.randint(1, 6)))
        elif pick < 0.86:
            rows.append("c %s" % ln)
        elif pick < 0.94:
            k = rng.randint(1, min(3, len(live)))
            rows.append("g %s" % ",".join(rng.sample(sorted(live), k)))
        else:
            rows.append("f")
    for ln in live:
        rows.append("c %s" % ln)
    rows.append("f")
    return rows


def _weave(rng):
    """Ranges shared until several claims stand on one block."""
    blocks = rng.choice([64, 96, 128])
    rows = ["dev %d" % blocks, "n a", "n b"]
    wide = rng.randint(10, 20)
    rows.append("w a/f 0 %d" % wide)
    size = {("a", "f"): wide, ("b", "g"): 0}
    for _ in range(rng.randint(16, 34)):
        pick = rng.random()
        if pick < 0.4:
            n = rng.randint(1, 5)
            at = rng.randint(0, max(0, size[("a", "f")] - n))
            to = rng.randint(0, size[("a", "f")])
            rows.append("s a/f %d %d a/f %d" % (at, n, to))
            size[("a", "f")] = max(size[("a", "f")], to + n)
        elif pick < 0.6:
            n = rng.randint(1, 5)
            at = rng.randint(0, max(0, size[("a", "f")] - n))
            to = rng.randint(0, size[("b", "g")])
            rows.append("s a/f %d %d b/g %d" % (at, n, to))
            size[("b", "g")] = max(size[("b", "g")], to + n)
        elif pick < 0.85:
            who = rng.choice([("a", "f"), ("b", "g")])
            if size[who] or who == ("a", "f"):
                at = rng.randint(0, size[who])
                n = rng.randint(1, 4)
                rows.append("w %s/%s %d %d" % (who[0], who[1], at, n))
                size[who] = max(size[who], at + n)
        elif pick < 0.93:
            rows.append("m a/f")
        else:
            rows.append("c a")
            rows.append("c b")
    rows.append("m a/f")
    rows.append("c a")
    rows.append("c b")
    rows.append("g a,b")
    rows.append("f")
    return rows


def _vacuum(rng):
    """Defragmenting items that are shared and items that are not."""
    blocks = rng.choice([48, 64, 96])
    rows = ["dev %d" % blocks, "n a"]
    names = ITEMS[:rng.randint(2, 4)]
    for nm in names:
        rows.append("w a/%s 0 %d" % (nm, rng.randint(3, 8)))
    live = ["a"]
    for _ in range(rng.randint(12, 26)):
        pick = rng.random()
        nm = rng.choice(names)
        ln = rng.choice(live)
        if pick < 0.3:
            rows.append("v %s/%s" % (ln, nm))
            rows.append("m %s/%s" % (ln, nm))
        elif pick < 0.45:
            rows.append("w %s/%s %d %d" % (ln, nm, rng.randint(0, 4), rng.randint(1, 5)))
        elif pick < 0.58 and len(live) < 4:
            dst = LINES[len(live)]
            rows.append("p %s %s" % (ln, dst))
            live.append(dst)
        elif pick < 0.68:
            other = rng.choice(names)
            rows.append("s %s/%s 0 %d %s/%s 0" % (ln, nm, rng.randint(1, 3), ln, other))
        elif pick < 0.78:
            rows.append("x %s/%s" % (ln, nm))
            rows.append("w %s/%s 0 %d" % (ln, nm, rng.randint(2, 6)))
        elif pick < 0.9:
            rows.append("f")
        else:
            rows.append("c %s" % ln)
    for ln in live:
        rows.append("c %s" % ln)
    rows.append("f")
    return rows


def _sets(rng):
    """Lines that share by descent, asked what a set of them would free."""
    blocks = rng.choice([128, 192, 256])
    rows = ["dev %d" % blocks, "n a"]
    for nm in ITEMS[:3]:
        rows.append("w a/%s 0 %d" % (nm, rng.randint(4, 10)))
    live = ["a"]
    for _ in range(rng.randint(3, 5)):
        src = rng.choice(live)
        dst = LINES[len(live)]
        rows.append("p %s %s" % (src, dst))
        live.append(dst)
        for _ in range(rng.randint(1, 3)):
            rows.append("w %s/%s %d %d" % (dst, rng.choice(ITEMS[:3]),
                                           rng.randint(0, 4), rng.randint(1, 4)))
    for _ in range(rng.randint(10, 20)):
        pick = rng.random()
        if pick < 0.45:
            k = rng.randint(1, min(3, len(live)))
            rows.append("g %s" % ",".join(rng.sample(sorted(live), k)))
        elif pick < 0.7:
            rows.append("c %s" % rng.choice(live))
        elif pick < 0.85:
            ln = rng.choice(live)
            rows.append("w %s/%s %d %d" % (ln, rng.choice(ITEMS[:3]),
                                           rng.randint(0, 6), rng.randint(1, 4)))
        elif pick < 0.93 and len(live) > 2:
            gone = rng.choice(live[1:])
            rows.append("d %s" % gone)
            live.remove(gone)
        else:
            rows.append("f")
    for ln in live:
        rows.append("c %s" % ln)
    rows.append("g %s" % ",".join(sorted(live)))
    return rows


def _wide(rng):
    """Charges asked thousands of times of a line standing on thousands of spans."""
    items = rng.choice([16000, 18000, 20000])
    unit = 4
    rows = ["dev 262144", "n a"]
    for k in range(items):
        rows.append("w a/i%d 0 %d" % (k, unit))
    rows.append("p a b")
    for k in range(0, items, 3):
        rows.append("w b/i%d 0 %d" % (k, unit))
    for k in range(21000):
        if k % 7 == 6:
            rows.append("w a/i%d %d 2" % (rng.randrange(items), rng.randrange(unit - 1)))
        elif k % 5 == 0:
            rows.append("u %s" % ("a" if k % 2 else "b"))
        else:
            rows.append("c %s" % ("a" if k % 2 else "b"))
    rows.append("g a,b")
    rows.append("c a")
    rows.append("c b")
    rows.append("u a")
    rows.append("u b")
    rows.append("f")
    return rows


def _churn(rng):
    """Allocation against a free map cut into thousands of runs."""
    unit = 4
    count = rng.choice([30000, 32000, 34000])
    rows = ["dev 262144", "n a"]
    for k in range(count):
        rows.append("w a/i%d 0 %d" % (k, unit))
    for k in range(0, count, 2):
        rows.append("x a/i%d" % k)
    rows.append("f")
    for k in range(50000):
        nm = "j%d" % k
        rows.append("w a/%s 0 %d" % (nm, rng.choice([1, 2, 3, 5, 7])))
        if k % 5 == 4:
            rows.append("x a/j%d" % (k - 2))
        if k % 2500 == 2499:
            rows.append("f")
    rows.append("f")
    rows.append("c a")
    return rows


def _fam(rng):
    """Stamp trees that lose lines, shares across families, and the family questions."""
    blocks = rng.choice([64, 96, 128])
    rows = ["dev %d" % blocks, "n a"]
    names = ITEMS[:rng.randint(2, 3)]
    for nm in names:
        rows.append("w a/%s 0 %d" % (nm, rng.randint(3, 6)))
    live = ["a"]
    dead = []
    nxt = 1
    for _ in range(rng.randint(16, 30)):
        pick = rng.random()
        if pick < 0.22 and nxt < len(LINES):
            dst = LINES[nxt]
            nxt += 1
            rows.append("p %s %s" % (rng.choice(live), dst))
            live.append(dst)
        elif pick < 0.32 and len(live) > 2:
            gone = rng.choice(live)
            rows.append("d %s" % gone)
            live.remove(gone)
            dead.append(gone)
        elif pick < 0.37 and dead:
            back = dead.pop(rng.randrange(len(dead)))
            rows.append("n %s" % back)
            live.append(back)
            rows.append("w %s/%s 0 %d" % (back, rng.choice(names), rng.randint(1, 3)))
        elif pick < 0.48 and nxt + 1 < len(LINES):
            src = rng.choice(live)
            nm = rng.choice(names)
            rows.append("w %s/%s 0 %d" % (src, nm, rng.randint(2, 4)))
            for _ in range(2):
                dst = LINES[nxt]
                nxt += 1
                rows.append("p %s %s" % (src, dst))
                live.append(dst)
            rows.append("w %s/%s 0 %d" % (src, nm, rng.randint(1, 3)))
        elif pick < 0.58:
            rows.append("w %s/%s %d %d" % (rng.choice(live), rng.choice(names),
                                           rng.randint(0, 3), rng.randint(1, 3)))
        elif pick < 0.66 and nxt < len(LINES):
            z = LINES[nxt]
            nxt += 1
            rows.append("n %s" % z)
            src = rng.choice(live)
            live.append(z)
            rows.append("s %s/%s 0 %d %s/%s 0" % (src, rng.choice(names), rng.randint(1, 3),
                                                  z, rng.choice(names)))
        elif pick < 0.84:
            rows.append("u %s" % rng.choice(live))
        elif pick < 0.94:
            rows.append("c %s" % rng.choice(live))
        else:
            k = rng.randint(1, min(3, len(live)))
            rows.append("g %s" % ",".join(rng.sample(sorted(live), k)))
    for ln in live:
        rows.append("u %s" % ln)
        rows.append("c %s" % ln)
    rows.append("g %s" % ",".join(sorted(live)))
    return rows


def _tree(rng):
    """The family questions asked thousands of times of a stamp tree that keeps losing lines.

    Two hundred and forty stamps of a line of nine hundred items, asked mostly about the lines
    near the top, so the family of the question stands on a hundred thousand spans and a walk
    over them dies. A table keyed by standing set survives it, and is a correct variant.
    """
    items = rng.choice(TREE_ITEMS)
    unit = 2
    rows = ["dev 65536", "n l0"]
    for k in range(items):
        rows.append("w l0/i%d 0 %d" % (k, unit))
    kin = ["l0"]
    roots = []
    nxt = 1
    for rnd in range(TREE_STAMPS):
        src = rng.choice(kin[-8:]) if rng.random() < 0.5 else rng.choice(kin)
        new = "l%d" % nxt
        nxt += 1
        rows.append("p %s %s" % (src, new))
        kin.append(new)
        for _ in range(TREE_WRITES):
            who = rng.choice(kin[-30:]) if rng.random() < 0.5 else rng.choice(kin)
            rows.append("w %s/i%d %d 1" % (who, rng.randrange(items), rng.randrange(unit)))
        if rnd % 8 == 7 and len(kin) > 6:
            gone = rng.choice(kin[1:-3])
            rows.append("d %s" % gone)
            kin.remove(gone)
        if rnd % 40 == 39:
            z = "z%d" % rnd
            rows.append("n %s" % z)
            roots.append(z)
            rows.append("s %s/i%d 0 %d %s/g 0" % (rng.choice(kin), rng.randrange(items),
                                                  unit, z))
        live = kin + roots
        for _ in range(TREE_ASKS):
            pick = rng.random()
            if pick < 0.55:
                who = rng.choice(kin[:8]) if rng.random() < 0.6 else rng.choice(live)
                rows.append("u %s" % who)
            elif pick < 0.98:
                rows.append("c %s" % rng.choice(live))
            else:
                rows.append("g %s" % ",".join(rng.sample(sorted(live), min(3, len(live)))))
    for ln in kin + roots:
        rows.append("u %s" % ln)
        rows.append("c %s" % ln)
    rows.append("f")
    return rows


MAKE = {
    "plain": _plain,
    "place": _place,
    "tight": _tight,
    "frag": _frag,
    "stampy": _stampy,
    "weave": _weave,
    "vacuum": _vacuum,
    "sets": _sets,
    "fam": _fam,
    "wide": _wide,
    "churn": _churn,
    "tree": _tree,
}


def programs(seed, per):
    out = []
    for fam, small in FAMILIES:
        count = per if small else BIG
        for k in range(count):
            rng = random.Random("%s|%s|%d" % (seed, fam, k))
            out.append((fam, "%s-%03d" % (fam, k), MAKE[fam](rng)))
    return out
