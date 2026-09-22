"""Programs generated from a seed drawn after the agent's container is gone.

Each family concentrates one mechanism. An unshaped population barely exercises this task:
measured on 1440 programs of the plain family, the reading that decides freshness from the
query's constants moved none of them and the per-rule union moved 3, while on 200 programs of
each family shaped for them the first moves 58% of meet and 28% of datacov, and the second 59%
of union. The two scale families exist for the wall clock, not for a rule.

  plain    small mixed programs: every construct, nothing concentrated
  cover    a label with a few allowed values joining a table that holds each of them
  datacov  a mid-size integer column every value of which the rows already use
  meet     a label sitting in two columns whose allowed sets differ
  union    rules that between them ask for every value a status column allows
  pigeon   labels that share a handful of spare values
  trade    an inequality on a label with spare values beside a join on the same label
  ne       inequalities against constants, on constants, on few-valued and on wide labels
  heads    rows whose answer column is itself a label: one-valued, few-valued and wide
  order    heads mixing integers and symbols, repeated variables, wildcards
  wide     one long program: thousands of labels over ranges of a billion values
  flags    rows each derived through dozens of like-shaped groups of two-valued labels
"""
import random

BIG = 999_999_999

FAMILIES = (
    ("plain", False),
    ("cover", False),
    ("datacov", False),
    ("meet", False),
    ("union", False),
    ("pigeon", False),
    ("trade", False),
    ("ne", False),
    ("heads", False),
    ("order", False),
    ("wide", True),
    ("flags", True),
)

BIG_PER = 3
SYMS = ("amber", "birch", "cedar", "dune", "elm", "fern", "gale", "heath")


class Namer:
    def __init__(self, prefix):
        self.prefix = prefix
        self.n = 0

    def __call__(self):
        self.n += 1
        return "?%s%d" % (self.prefix, self.n)


# --------------------------------------------------------------------------- small families

def plain(rng):
    L = []
    tabs = []
    for ti in range(rng.randint(2, 4)):
        cols = []
        for _ in range(rng.randint(1, 3)):
            k = rng.random()
            if k < 0.3:
                cols.append(("sym", rng.sample(SYMS, rng.randint(2, 4))))
            elif k < 0.6:
                lo = rng.randint(0, 3)
                cols.append(("int", lo, lo + rng.randint(1, 5)))
            else:
                cols.append(("int", 0, BIG))
        name = "t%d" % ti
        tabs.append((name, cols))
        L.append("table %s %s" % (name, " ".join(dom_text(c) for c in cols)))
    labs = ["?u%d" % i for i in range(rng.randint(1, 6))]
    for name, cols in tabs:
        for _ in range(rng.randint(1, 6)):
            vals = []
            for c in cols:
                if rng.random() < 0.35:
                    vals.append(rng.choice(labs))
                else:
                    vals.append(pick_const(rng, c))
            L.append("row %s %s" % (name, " ".join(vals)))
    L += random_rules(rng, tabs, "q", rng.randint(1, 3))
    return fix_labels(L)


def cover(rng):
    n = rng.randint(2, 6)
    mgrs = rng.sample(SYMS, 3)
    L = ["table cust 0..%d 1..%d" % (BIG, n), "table reg 1..%d %s" % (n, "|".join(mgrs))]
    ids = rng.sample(range(1, min(500, BIG)), rng.randint(2, 4))
    lab = Namer("r")
    for c in ids:
        L.append("row cust %d %s" % (c, lab() if rng.random() < 0.7 else rng.randint(1, n)))
    main = rng.choice(mgrs)
    for v in range(1, n + 1):
        if rng.random() < 0.85:
            L.append("row reg %d %s" % (v, main if rng.random() < 0.8 else rng.choice(mgrs)))
        if rng.random() < 0.2:
            L.append("row reg %d %s" % (v, rng.choice(mgrs)))
    L.append("rule boss X M :- cust(X, R), reg(R, M)")
    if rng.random() < 0.5:
        L.append("rule boss X M :- cust(X, R), reg(R, M), M != %s" % rng.choice(mgrs))
    if rng.random() < 0.5:
        L.append("rule some X :- cust(X, R), reg(R, %s)" % main)
    return L


def datacov(rng):
    n = rng.randint(6, 14)
    L = ["table ship 0..%d 1..%d" % (BIG, n), "table zone 1..%d %s" % (n, "|".join(SYMS[:3]))]
    lab = Namer("z")
    for s in rng.sample(range(1, min(900, BIG)), rng.randint(1, 3)):
        L.append("row ship %d %s" % (s, lab()))
    gap = rng.random() < 0.4
    tag = rng.choice(SYMS[:3])
    for v in range(1, n + 1):
        if gap and v == rng.randint(1, n):
            continue
        L.append("row zone %d %s" % (v, tag if rng.random() < 0.85 else rng.choice(SYMS[:3])))
    L.append("rule land S T :- ship(S, Z), zone(Z, T)")
    if rng.random() < 0.4:
        L.append("rule any S :- ship(S, _)")
    return L


def meet(rng):
    a = rng.randint(3, 7)
    b = rng.randint(2, a - 1)
    L = ["table cust 0..%d 1..%d" % (BIG, a), "table seen 1..%d" % b,
         "table reg 1..%d %s" % (a, "|".join(SYMS[:2]))]
    lab = Namer("r")
    x = lab()
    L.append("row cust 7 %s" % x)
    L.append("row seen %s" % x)
    if rng.random() < 0.4:
        y = lab()
        L.append("row cust 8 %s" % y)
    for v in range(1, b + 1):
        if rng.random() < 0.9:
            L.append("row reg %d %s" % (v, SYMS[0]))
    for v in range(b + 1, a + 1):
        if rng.random() < 0.6:
            L.append("row reg %d %s" % (v, SYMS[1]))
    L.append("rule boss X M :- cust(X, R), reg(R, M)")
    return L


def union(rng):
    st = rng.sample(SYMS, rng.randint(2, 4))
    L = ["table acct 0..%d %s" % (BIG, "|".join(st)), "table hold 0..%d" % BIG]
    lab = Namer("s")
    ids = rng.sample(range(1, min(400, BIG)), rng.randint(2, 5))
    for i in ids:
        L.append("row acct %d %s" % (i, lab() if rng.random() < 0.7 else rng.choice(st)))
        if rng.random() < 0.3:
            L.append("row hold %d" % i)
    asked = st[:] if rng.random() < 0.6 else rng.sample(st, len(st) - 1)
    held = rng.choice(asked) if rng.random() < 0.4 else None
    for s in asked:
        if s == held:
            L.append("rule live A :- acct(A, %s), hold(A)" % s)
        else:
            L.append("rule live A :- acct(A, %s)" % s)
    if rng.random() < 0.3:
        L.append("rule live A :- acct(A, S), S != %s" % rng.choice(st))
    return L


def pigeon(rng):
    hi = rng.randint(2, 4)
    L = ["table slot 0..9 1..%d" % hi, "table used 1..%d" % hi]
    k = rng.randint(2, 3)
    labs = ["?p%d" % i for i in range(k)]
    for i, l in enumerate(labs):
        L.append("row slot %d %s" % (i, l))
    for v in rng.sample(range(1, hi + 1), rng.randint(0, hi - 1)):
        L.append("row used %d" % v)
    L.append("rule clash :- slot(_, V), used(V)")
    L.append("rule clash :- slot(0, V), slot(1, V)")
    if k == 3:
        L.append("rule clash :- slot(1, V), slot(2, V)")
        if rng.random() < 0.7:
            L.append("rule clash :- slot(0, V), slot(2, V)")
    if rng.random() < 0.4:
        L.append("rule who X :- slot(X, V), used(V)")
    return L


def trade(rng):
    k = rng.randint(0, 4)
    L = ["table leg 0..%d 0..%d" % (BIG, BIG), "table stop 0..%d" % BIG,
         "table far 0..%d 0..%d" % (BIG, BIG)]
    lab = Namer("d")
    d = lab()
    L.append("row leg 1 %s" % d)
    if rng.random() < 0.5:
        L.append("row leg 2 %s" % lab())
    if rng.random() < 0.5:
        L.append("row leg 3 %d" % rng.randint(0, 6))
    for _ in range(rng.randint(0, 2)):
        L.append("row stop %d" % rng.choice([k, rng.randint(0, 6)]))
    if rng.random() < 0.5:
        L.append("row far %s %d" % (d, rng.randint(0, 6)))
    L.append("rule go L :- leg(L, D), D != %d" % k)
    L.append("rule go L :- leg(L, D), stop(D)")
    if rng.random() < 0.4:
        L.append("rule go L :- leg(L, D), far(D, %d)" % rng.randint(0, 6))
    if rng.random() < 0.4:
        L.append("rule at L D :- leg(L, D), stop(D)")
    return L


def ne(rng):
    st = rng.sample(SYMS, 3)
    L = ["table acct 0..%d %s 0..%d" % (BIG, "|".join(st), BIG), "table hold 0..%d" % BIG]
    lab = Namer("n")
    for i in rng.sample(range(1, min(300, BIG)), rng.randint(2, 5)):
        s = lab() if rng.random() < 0.6 else rng.choice(st)
        v = lab() if rng.random() < 0.4 else str(rng.randint(0, 5))
        L.append("row acct %d %s %s" % (i, s, v))
        if rng.random() < 0.3:
            L.append("row hold %d" % i)
    a, b = rng.sample(st, 2)
    L.append("rule keep A :- acct(A, S, _), S != %s" % a)
    if rng.random() < 0.6:
        L.append("rule keep A :- acct(A, %s, _), hold(A)" % a)
    L.append("rule real A :- acct(A, _, V), V != 0")
    if rng.random() < 0.5:
        L.append("rule real A :- acct(A, _, 0)")
    if rng.random() < 0.5:
        L.append("rule both A :- acct(A, S, V), S != %s, V != %d" % (b, rng.randint(0, 5)))
    return L


def heads(rng):
    L = ["table tag 0..%d %s" % (BIG, "|".join(SYMS[:3])), "table one 0..%d 7..7" % BIG,
         "table num 0..%d 0..%d" % (BIG, BIG)]
    lab = Namer("h")
    for i in range(rng.randint(1, 4)):
        L.append("row tag %d %s" % (i, lab() if rng.random() < 0.6 else rng.choice(SYMS[:3])))
    for i in range(rng.randint(1, 3)):
        L.append("row one %d %s" % (i, lab() if rng.random() < 0.7 else "7"))
    for i in range(rng.randint(1, 3)):
        L.append("row num %d %s" % (i, lab() if rng.random() < 0.6 else str(rng.randint(0, 9))))
    L.append("rule what T :- tag(_, T)")
    L.append("rule sev K V :- one(K, V)")
    L.append("rule val V :- num(_, V)")
    if rng.random() < 0.5:
        L.append("rule what T :- tag(_, T), T != %s" % rng.choice(SYMS[:3]))
    return L


def order(rng):
    L = ["table kv 0..30 %s" % "|".join(SYMS[:4]), "table pair 0..30 0..30"]
    lab = Namer("o")
    for _ in range(rng.randint(3, 7)):
        L.append("row kv %d %s" % (rng.randint(0, 30), lab() if rng.random() < 0.2 else rng.choice(SYMS[:4])))
    for _ in range(rng.randint(2, 6)):
        a = lab() if rng.random() < 0.25 else str(rng.randint(0, 30))
        L.append("row pair %s %d" % (a, rng.randint(0, 30)))
    L.append("rule mix X Y :- kv(X, Y)")
    L.append("rule mix Y X :- pair(X, Y)")
    L.append("rule loop X :- pair(X, X)")
    L.append("rule dup X X :- pair(X, _)")
    return fix_labels(L)


# --------------------------------------------------------------------------- scale families

def wide(rng, ncust=5000, nord=9000):
    L = ["table cust 0..%d 1..40 0..%d" % (BIG, BIG),
         "table reg 1..40 %s" % "|".join(SYMS[:4]),
         "table ord 0..%d 0..%d 0..%d open|shut|held" % (BIG, BIG, BIG),
         "table ship 0..%d 0..%d" % (BIG, BIG),
         "table hold 0..%d" % BIG]
    lab = Namer("w")
    ids = rng.sample(range(10, BIG), ncust)
    for c in ids:
        r = lab() if rng.random() < 0.15 else str(rng.randint(1, 40))
        s = lab() if rng.random() < 0.3 else str(rng.randint(0, BIG))
        L.append("row cust %d %s %s" % (c, r, s))
    east = set(rng.sample(range(1, 41), 20))
    odd = rng.randint(1, 40)
    for g in range(1, 41):
        L.append("row reg %d %s" % (g, SYMS[0] if g in east else SYMS[1]))
    L.append("row reg %d %s" % (odd, SYMS[2]))
    for o in rng.sample(range(10, BIG), nord):
        c = lab() if rng.random() < 0.2 else str(rng.choice(ids))
        a = lab() if rng.random() < 0.25 else str(rng.randint(0, 1000))
        st = lab() if rng.random() < 0.03 else rng.choice(["open", "shut", "held"])
        L.append("row ord %d %s %s %s" % (o, c, a, st))
        if rng.random() < 0.5:
            d = lab() if rng.random() < 0.3 else str(rng.randint(0, 50))
            L.append("row ship %d %s" % (o, d))
        if rng.random() < 0.05:
            L.append("row hold %d" % o)
    L.append("rule east X :- cust(X, R, _), reg(R, %s)" % SYMS[0])
    L.append("rule east X :- cust(X, R, _), reg(R, %s)" % SYMS[1])
    L.append("rule far O :- ship(O, D), D != 0")
    L.append("rule far O :- ship(O, 0), hold(O)")
    L.append("rule paid X A :- ord(_, X, A, shut), cust(X, _, _)")
    L.append("rule live O :- ord(O, _, _, open)")
    L.append("rule live O :- ord(O, _, _, held)")
    L.append("rule live O :- ord(O, _, _, S), S != open, hold(O)")
    return L


def flags(rng, ncust=40, per=30):
    """Every account has three two-valued unknowns and two policy rows of each kind, so every
    group of conditions a customer's row collects has the same shape: four conditions, the
    status in all four, each other unknown in two, each value twice. Only the constants
    decide whether a group holds under every assignment (a covering account) or fails under
    two of its eight (every other account). A search that does not split the groups apart
    sees nothing to tell the covering one from the rest, and explores two cases per group it
    meets first."""
    L = ["table acct 0..%d 0..%d open|shut gold|base east|west" % (BIG, BIG),
         "table pa 0..%d open|shut gold|base" % BIG,
         "table pb 0..%d open|shut east|west" % BIG]
    lab = Namer("f")
    aid = 100
    for c in range(1, ncust + 1):
        good = rng.random() < 0.5
        pos = rng.randint(per // 2, per - 1)
        for k in range(per):
            aid += 1
            L.append("row acct %d %d %s %s %s" % (aid, c, lab(), lab(), lab()))
            if good and k == pos:
                pa = [("open", "gold"), ("open", "base")]
                pb = [("shut", "east"), ("shut", "west")]
            else:
                pa = [("open", "gold"), ("shut", "base")]
                pb = [("open", "west"), ("shut", "east")]
                if rng.random() < 0.5:
                    pa = [("open", "base"), ("shut", "gold")]
                    pb = [("open", "east"), ("shut", "west")]
            for s, t in pa:
                L.append("row pa %d %s %s" % (aid, s, t))
            for s, t in pb:
                L.append("row pb %d %s %s" % (aid, s, t))
    L.append("rule live C :- acct(A, C, S, T, _), pa(A, S, T)")
    L.append("rule live C :- acct(A, C, S, _, R), pb(A, S, R)")
    return L


# --------------------------------------------------------------------------- helpers

def dom_text(c):
    if c[0] == "sym":
        return "|".join(c[1])
    return "%d..%d" % (c[1], c[2])


def pick_const(rng, c):
    if c[0] == "sym":
        return rng.choice(c[1])
    if c[2] - c[1] > 100:
        return str(rng.randint(0, 12))
    return str(rng.randint(c[1], c[2]))


def random_rules(rng, tabs, prefix, nq):
    out = []
    for qi in range(nq):
        q = "%s%d" % (prefix, qi)
        arity = rng.randint(0, 2)
        made = 0
        for _ in range(12):
            if made >= rng.randint(1, 3):
                break
            atoms, used, where = [], [], {}
            for _a in range(rng.randint(1, 3)):
                name, cols = rng.choice(tabs)
                args = []
                for ci, c in enumerate(cols):
                    k = rng.random()
                    if k < 0.6:
                        v = rng.choice("XYZ")
                        args.append(v)
                        used.append(v)
                        where.setdefault(v, c)
                    elif k < 0.8:
                        args.append("_")
                    else:
                        args.append(pick_const(rng, c))
                atoms.append("%s(%s)" % (name, ", ".join(args)))
            used = sorted(set(used))
            if len(used) < arity:
                continue
            head = rng.sample(used, arity)
            conds = []
            if used and rng.random() < 0.4:
                v = rng.choice(used)
                conds.append("%s != %s" % (v, pick_const(rng, where[v])))
            out.append("rule %s %s:- %s" % (q, "".join(h + " " for h in head),
                                            ", ".join(atoms + conds)))
            made += 1
    return out


def fix_labels(lines):
    """Drop rows whose labels sit in columns with nothing in common, so every label allows a
    value; the loader would reject nothing, but the program would have no filling at all."""
    cols = {}
    for line in lines:
        p = line.split()
        if p[0] == "table":
            cols[p[1]] = [parse_dom(x) for x in p[2:]]
    allowed = {}
    keep = []
    for line in lines:
        p = line.split()
        if p[0] != "row":
            keep.append(line)
            continue
        trial = dict(allowed)
        ok = True
        for d, v in zip(cols[p[1]], p[2:]):
            if v.startswith("?"):
                cur = trial.get(v, d)
                cur = meet_dom(cur, d)
                if cur is None:
                    ok = False
                    break
                trial[v] = cur
        if ok:
            allowed = trial
            keep.append(line)
    return keep


def parse_dom(x):
    if ".." in x:
        a, b = x.split("..")
        return ("int", int(a), int(b))
    return ("sym", tuple(x.split("|")))


def meet_dom(a, b):
    if a[0] == "int" and b[0] == "int":
        lo, hi = max(a[1], b[1]), min(a[2], b[2])
        return ("int", lo, hi) if lo <= hi else None
    if a[0] == "sym" and b[0] == "sym":
        s = tuple(x for x in a[1] if x in b[1])
        return ("sym", s) if s else None
    return None


BUILDERS = {
    "plain": plain, "cover": cover, "datacov": datacov, "meet": meet, "union": union,
    "pigeon": pigeon, "trade": trade, "ne": ne, "heads": heads, "order": order,
    "wide": wide, "flags": flags,
}


def programs(seed, per):
    """Every generated program: (family, name, lines), in a fixed order for a given seed."""
    out = []
    for fam, big in FAMILIES:
        count = BIG_PER if big else per
        for i in range(count):
            rng = random.Random("%s/%s/%d" % (seed, fam, i))
            out.append((fam, "%s-%03d" % (fam, i), BUILDERS[fam](rng)))
    return out
