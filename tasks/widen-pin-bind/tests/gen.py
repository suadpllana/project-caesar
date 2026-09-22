"""Programs generated from a seed drawn after the agent's container is gone.

The families are shaped around the decisions rather than sampled from the space of programs.
An unshaped population binds almost everything to the only entry that fits, so the comparison
never has two survivors to compare, no open entry is ever settled twice and every wrong
reading prints what the right one does. Each family below concentrates one mechanism.

  plain    ordinary programs: several entries fit, one of them is better everywhere
  cross    entries built to cross - cheaper at one slot, dearer at another, totals apart
  ret      entries that tie on every slot and part on the kind they give back
  opens    open entries over lattices with one least common kind, with two, and with a
           bound the slots meet above
  pins     several expressions over the same open entries, so a pin decides the later ones,
           with an entry whose open slot sits to the right of a plain one
  drop     a trial that would settle an entry and then loses the call
  stale    one call reached twice under pins that differ, asking for the same kind
  paths    two chains of different lengths between the same pair of kinds
  deep     one expression nesting calls sixteen deep, three entries at every name
  wide     several hundred expressions over one declaration set

`deep` and `wide` exist for the execution limit rather than for a rule.
"""
import random

FAMILIES = (
    ("plain", False),
    ("cross", False),
    ("ret", False),
    ("opens", False),
    ("pins", False),
    ("drop", False),
    ("stale", False),
    ("paths", False),
    ("deep", True),
    ("wide", True),
)

BIG = 3


# --- kinds -------------------------------------------------------------------------------

def _lattice(rng, layers, width, skip=True):
    """A layered rise graph, with a single top kind, returned as (names, edges)."""
    rows = []
    n = 0
    for lay in range(layers):
        wide = 1 if lay == layers - 1 else max(1, width - (lay // 2))
        rows.append(["k%d" % (n + i) for i in range(wide)])
        n += wide
    edges = []
    for lay in range(layers - 1):
        for one in rows[lay]:
            up = rng.sample(rows[lay + 1], min(len(rows[lay + 1]),
                                               1 if rng.random() < 0.6 else 2))
            for other in up:
                edges.append((one, other))
            if skip and lay + 2 < layers and rng.random() < 0.35:
                edges.append((one, rng.choice(rows[lay + 2])))
    return rows, edges


def _close(names, edges):
    """Steps between every ordered pair of kinds."""
    up = {k: [] for k in names}
    for a, b in edges:
        up[a].append(b)
    far = {(k, k): 0 for k in names}
    for a, b in edges:
        if far.get((a, b), 99) > 1:
            far[(a, b)] = 1
    moved = True
    while moved:
        moved = False
        for (a, b), d in list(far.items()):
            for c in up[b]:
                if far.get((a, c), 99) > d + 1:
                    far[(a, c)] = d + 1
                    moved = True
    return far


def _over(far, names, one):
    return [k for k in names if (one, k) in far]


def _under(far, names, one):
    return [k for k in names if (k, one) in far]


# --- declarations ------------------------------------------------------------------------

class Deck:
    """The declarations of one program, and enough about them to build expressions."""

    def __init__(self, rng, rows, edges):
        self.rng = rng
        self.rows = rows
        self.names = [k for row in rows for k in row]
        self.edges = edges
        self.far = _close(self.names, edges)
        self.ents = []
        self.vals = {}
        self.top = rows[-1][0]

    def val(self, kind):
        for name, was in self.vals.items():
            if was == kind and self.rng.random() < 0.5:
                return name
        name = "v%d" % len(self.vals)
        self.vals[name] = kind
        return name

    def entry(self, name, ret, params, bound=None):
        self.ents.append({"name": name, "ret": ret, "par": list(params),
                          "open": bound is not None, "bound": bound})
        return len(self.ents) - 1

    def of(self, name, count):
        return [e for e in self.ents
                if e["name"] == name and len(e["par"]) == count]

    def lines(self):
        out = ["kind %s" % k for k in self.names]
        out += ["rise %s %s" % (a, b) for a, b in self.edges]
        for ent in self.ents:
            if ent["open"]:
                out.append("open %s %s %s %s"
                           % (ent["name"], ent["bound"], ent["ret"], " ".join(ent["par"])))
            else:
                out.append("entry %s %s %s"
                           % (ent["name"], ent["ret"], " ".join(ent["par"])))
        out += ["val %s %s" % (n, k) for n, k in self.vals.items()]
        return out


def _near(deck, kind, spread=2):
    """A kind the given one rises to, usually the kind itself or one step up."""
    rng = deck.rng
    over = [k for k in _over(deck.far, deck.names, kind)
            if deck.far[(kind, k)] <= spread]
    weights = [4 if k == kind else 2 if deck.far[(kind, k)] == 1 else 1 for k in over]
    return rng.choices(over, weights=weights)[0]


def _pool(deck, count, arity):
    """A pool of names, each with several entries whose slots overlap.

    One entry of every name sits exactly on the centre, so an argument standing there is
    always taken by something; the rest sit a step or two above it, which is what gives a
    call two survivors to compare. Entries that would repeat a slot list are dropped: two
    entries alike in every kind can never be told apart and would make the call ambiguous
    wherever it appears.
    """
    rng = deck.rng
    made = []
    for i in range(count):
        name = "f%d" % i
        n = arity if isinstance(arity, int) else rng.choice(arity)
        centre = [rng.choice(deck.names[:-1]) for _ in range(n)]
        back = rng.choice(deck.names)
        seen = set()
        deck.entry(name, back, centre)
        seen.add(tuple(centre))
        for _ in range(rng.randint(1, 3)):
            params = [_near(deck, c) if rng.random() < 0.8 else rng.choice(deck.names)
                      for c in centre]
            if tuple(params) in seen:
                continue
            seen.add(tuple(params))
            ret = back if rng.random() < 0.5 else _near(deck, back)
            deck.entry(name, ret, params)
        made.append((name, n))
    return made


# --- expressions -------------------------------------------------------------------------

def _stand(deck, want):
    """A kind an argument may stand at so that a slot asking for `want` can take it."""
    under = _under(deck.far, deck.names, want)
    weights = [4 if k == want else 2 if deck.far[(k, want)] == 1 else 1 for k in under]
    return deck.rng.choices(under, weights=weights)[0]


def _call(deck, pool, name, want, depth):
    """An expression for `name` whose result can stand where `want` is asked for."""
    rng = deck.rng
    ents = [e for e in deck.ents if e["name"] == name]
    fit = [e for e in ents
           if want is None or e["ret"] == "*" or (e["ret"], want) in deck.far]
    guide = rng.choice(fit or ents)
    args = []
    for slot in guide["par"]:
        if slot == "*":
            asks = rng.choice(_under(deck.far, deck.names, guide["bound"]))
        else:
            asks = slot
        stands = _stand(deck, asks)
        if depth <= 0 or rng.random() < 0.45:
            args.append(deck.val(stands))
            continue
        below = [(other, n) for other, n in pool
                 if any(e["ret"] == stands or e["ret"] == "*"
                        or (e["ret"], stands) in deck.far
                        for e in deck.ents if e["name"] == other)]
        if not below:
            args.append(deck.val(stands))
            continue
        other, _n = rng.choice(below)
        args.append(_call(deck, pool, other, stands, depth - 1))
    return "%s(%s)" % (name, ",".join(args))


# --- families ----------------------------------------------------------------------------

def _plain(rng, asks=3, depth=2, arity=(1, 2), layers=4, width=4):
    rows, edges = _lattice(rng, layers, width)
    deck = Deck(rng, rows, edges)
    pool = _pool(deck, 4, arity)
    out = []
    for _ in range(asks):
        name, _n = rng.choice(pool)
        out.append(_call(deck, pool, name, None, depth))
    return deck, out


def _cross(rng):
    """Two entries that cross on two slots, with totals that differ.

    Crossing alone is not enough: where the two totals are equal, adding the costs up and
    taking the lowest comes out ambiguous as well, and the program separates nothing. One
    slot is put a single step up and the other two, so the totals are one and two and the
    reading that takes the cheapest total prints a binding where the answer is one word.
    """
    rows, edges = _lattice(rng, 4, 4)
    deck = Deck(rng, rows, edges)
    low = rows[0]
    a, b = rng.sample(low, 2) if len(low) > 1 else (low[0], low[0])

    def step(kind, want):
        over = [k for k in _over(deck.far, deck.names, kind) if deck.far[(kind, k)] == want]
        return rng.choice(over) if over else None

    near, far = step(a, 1), step(b, 2)
    if near is None or far is None:
        near, far = step(a, 1) or a, step(b, 1) or b
    deck.entry("f0", rng.choice(deck.names), [a, far])
    deck.entry("f0", rng.choice(deck.names), [near, b])
    if rng.random() < 0.5:
        deck.entry("f0", rng.choice(deck.names), [near, far])
    pool = [("f0", 2)] + _pool(deck, 2, (1, 2))
    out = ["f0(%s,%s)" % (deck.val(a), deck.val(b))]
    for _ in range(rng.randint(1, 2)):
        name, _n = rng.choice(pool)
        out.append(_call(deck, pool, name, None, 1))
    return deck, out


def _ret(rng):
    """Entries alike at every slot and apart in the kind they give back.

    `g0` takes the same kind twice over and gives back two different kinds, so the two
    vectors are equal at the slot and apart at the last number. Asked for nothing the call is
    ambiguous; asked for a kind by the slot above it, the entry that lands nearer wins.
    """
    rows, edges = _lattice(rng, 4, 4, skip=False)
    deck = Deck(rng, rows, edges)
    low = rng.choice(rows[0])
    over = [k for k in _over(deck.far, deck.names, low) if k != low]
    mid = rng.choice(over)
    far = [k for k in over if deck.far[(low, k)] > deck.far[(low, mid)]] or [mid]
    up = rng.choice(far)
    deck.entry("g0", low, [low])
    deck.entry("g0", mid, [low])
    if rng.random() < 0.5:
        deck.entry("g0", up, [low])
    deck.entry("f0", deck.top, [mid])
    deck.entry("h0", deck.top, [low])
    x = deck.val(low)
    out = ["f0(g0(%s))" % x, "g0(%s)" % x, "h0(g0(%s))" % x]
    rng.shuffle(out)
    return deck, out


def _opens(rng):
    """Open entries over lattices shaped three ways.

    A plain layered one, where the open slots usually meet at a single kind; a diamond, where
    two kinds have two common kinds with neither below the other and the entry settles at
    nothing; and one whose bound sits below where the slots meet, so an entry that would
    otherwise be taken is dropped. Without the last two, no generated program tells a binder
    that takes the first least kind, or one that never reads the bound, from the reference.
    """
    shape = rng.choice(["flat", "diamond", "bound"])
    if shape == "diamond":
        names = ["k%d" % i for i in range(5)]
        edges = [("k0", "k2"), ("k1", "k2"), ("k0", "k3"), ("k1", "k3"),
                 ("k2", "k4"), ("k3", "k4")]
        rows = [["k0", "k1"], ["k2", "k3"], ["k4"]]
        deck = Deck(rng, rows, edges)
        deck.names = names
        deck.far = _close(names, edges)
        deck.top = "k4"
    else:
        rows, edges = _lattice(rng, 4, 4, skip=False)
        deck = Deck(rng, rows, edges)
    top = deck.top
    slots = rng.choice([2, 2, 3])
    params = ["*"] * slots
    if rng.random() < 0.4:
        params.append(rng.choice(rows[1] if len(rows) > 1 else rows[0]))
    rng.shuffle(params)
    bound = rng.choice(rows[0]) if shape == "bound" else rng.choice([top] + rows[-2])
    deck.entry("f0", "*" if rng.random() < 0.6 else rng.choice(deck.names),
               params, bound=bound)
    fixed = [rng.choice(rows[0]) if p == "*" else p for p in params]
    if shape == "bound":
        # dearer at every slot, so an entry that kept its place by not reading the bound
        # would take the call away from it
        fixed = [_near(deck, k, 2) if p == "*" else p for k, p in zip(fixed, params)]
    deck.entry("f0", rng.choice(deck.names), fixed)
    pool = [("f0", len(params))] + _pool(deck, 2, (1, 2))
    out = []
    for _ in range(rng.randint(2, 3)):
        if shape == "bound":
            # the slots stand wherever they like rather than under the bound, which is the
            # only way a program says anything about an entry that never reads it
            args = [deck.val(rng.choice(deck.names[:-1])) if slot == "*"
                    else deck.val(_stand(deck, slot)) for slot in params]
            out.append("f0(%s)" % ",".join(args))
        else:
            out.append(_call(deck, pool, "f0", None, 1))
    return deck, out


def _pins(rng):
    """Several expressions over one open entry, so what the first one settles decides the rest."""
    rows, edges = _lattice(rng, 4, 4, skip=False)
    deck = Deck(rng, rows, edges)
    deck.entry("g0", deck.top, ["*", "*"], bound=deck.top)
    deck.entry("g0", rng.choice(rows[1] if len(rows) > 1 else rows[0]),
               [rng.choice(rows[0]), rng.choice(rows[0])])
    deck.entry("f0", "*", ["*"], bound=rng.choice(rows[-2] + [deck.top]))
    deck.entry("f0", rng.choice(deck.names), [rng.choice(rows[0])])
    plain = deck.top
    deck.entry("h0", "*", [plain, "*"], bound=deck.top)
    deck.entry("h0", rng.choice(deck.names), [plain, rng.choice(rows[0])])
    pool = [("g0", 2), ("f0", 1), ("h0", 2)]
    out = []
    for _ in range(rng.randint(3, 5)):
        name, _n = rng.choice(pool)
        out.append(_call(deck, pool, name, None, 1))
    deck.entry("p0", "*", ["*"], bound=deck.top)
    deck.entry("q0", "*", ["*"], bound=deck.top)
    for _ in range(rng.randint(1, 2)):
        out.append("h0(p0(%s),q0(%s))" % (deck.val(rng.choice(rows[0])),
                                          deck.val(rng.choice(rows[0]))))
    return deck, out


def _drop(rng):
    """A trial that settles an open entry and then loses the call to a plain one."""
    rows, edges = _lattice(rng, 4, 3, skip=False)
    deck = Deck(rng, rows, edges)
    a = rng.choice(rows[0])
    b = rng.choice([k for k in rows[0] if k != a] or [a])
    upb = _near(deck, b, 1)
    deck.entry("f0", "*", ["*", "*"], bound=deck.top)
    deck.entry("f0", rng.choice(deck.names), [a, upb])
    x, y = deck.val(a), deck.val(upb)
    out = ["f0(%s,%s)" % (x, y), "f0(%s,%s)" % (x, x)]
    if rng.random() < 0.5:
        out.append("f0(%s,%s)" % (y, y))
    return deck, out


def _stale(rng):
    """One call reached under two different pins, asking for the same kind both times."""
    rows, edges = _lattice(rng, 4, 3, skip=False)
    deck = Deck(rng, rows, edges)
    a = rng.choice(rows[0])
    b = _near(deck, a, 1)
    while b == a:
        rows, edges = _lattice(rng, 4, 3, skip=False)
        deck = Deck(rng, rows, edges)
        a = rng.choice(rows[0])
        b = _near(deck, a, 1)
    c = _near(deck, b, 1)
    deck.entry("w0", "*", ["*"], bound=deck.top)
    deck.entry("w0", b, [a])
    deck.entry("f0", deck.top, [a, b])
    deck.entry("f0", deck.top, [b, b])
    x, q = deck.val(a), deck.val(b)
    out = ["f0(w0(%s),w0(%s))" % (x, q)]
    if rng.random() < 0.5:
        out.append("f0(w0(%s),w0(%s))" % (q, x))
    out.append("w0(%s)" % deck.val(c))
    return deck, out


def _paths(rng):
    """Pairs of kinds joined by chains of two different lengths."""
    names = ["k%d" % i for i in range(6)]
    edges = [("k0", "k1"), ("k1", "k2"), ("k0", "k2"), ("k2", "k3"),
             ("k1", "k4"), ("k4", "k3"), ("k3", "k5"), ("k2", "k5")]
    rng.shuffle(edges)
    rows = [[n] for n in names]
    deck = Deck(rng, rows, edges)
    deck.names = names
    deck.far = _close(names, edges)
    deck.top = "k5"
    pool = _pool(deck, 3, (1, 2))
    out = []
    for _ in range(rng.randint(2, 3)):
        name, _n = rng.choice(pool)
        out.append(_call(deck, pool, name, None, 2))
    return deck, out


def _deep(rng):
    """One expression nesting sixteen calls, three entries fitting at every one of them.

    The kinds are a chain, every entry gives back its foot and takes a kind one, two or three
    steps up it, so all three are taken at every level and each asks the call below it for a
    different kind. Nothing about the answer is hard; the count is: a binder that tries the
    call below again for every entry above it does three to the sixteenth trials for this one
    expression.
    """
    n = rng.randint(6, 7)
    names = ["k%d" % i for i in range(n)]
    edges = [(names[i], names[i + 1]) for i in range(n - 1)]
    deck = Deck(rng, [[k] for k in names], edges)
    deck.names = names
    deck.far = _close(names, edges)
    deck.top = names[-1]
    foot = names[0]
    pool = []
    for i in range(3):
        name = "f%d" % i
        for step in rng.sample([1, 2, 3], 3):
            deck.entry(name, foot, [names[step]])
        pool.append(name)
    text = deck.val(foot)
    for _ in range(16):
        text = "%s(%s)" % (rng.choice(pool), text)
    return deck, [text]


def _wide(rng):
    """Three hundred expressions over one declaration set, each nesting six to nine calls.

    Open entries sit among the plain ones, so pins accumulate as the expressions are reached
    and what a call binds to depends on the ones before it. The depth is what costs: every
    expression is tried three ways at every level.
    """
    n = 6
    names = ["k%d" % i for i in range(n)]
    edges = [(names[i], names[i + 1]) for i in range(n - 1)]
    deck = Deck(rng, [[k] for k in names], edges)
    deck.names = names
    deck.far = _close(names, edges)
    deck.top = names[-1]
    foot = names[0]
    pool = []
    for i in range(3):
        name = "f%d" % i
        for step in rng.sample([1, 2, 3], 3):
            deck.entry(name, foot, [names[step]])
        pool.append(name)
    deck.entry("g0", "*", ["*"], bound=names[3])
    deck.entry("g0", foot, [names[2]])
    out = []
    for _ in range(300):
        text = deck.val(rng.choice(names[:2]))
        for _ in range(rng.randint(6, 9)):
            text = "%s(%s)" % (rng.choice(pool + ["g0"]), text)
        out.append(text)
    return deck, out


BUILD = {
    "plain": _plain, "cross": _cross, "ret": _ret, "opens": _opens, "pins": _pins,
    "drop": _drop, "stale": _stale, "paths": _paths, "deep": _deep, "wide": _wide,
}


def build(fam, rng):
    deck, asks = BUILD[fam](rng)
    return deck.lines() + ["ask %s" % one for one in asks]


def programs(seed, per):
    """Every graded program for this run, as (family, name, lines)."""
    out = []
    for fam, big in FAMILIES:
        count = BIG if big else per
        for i in range(count):
            rng = random.Random("%s|%s|%d" % (seed, fam, i))
            out.append((fam, "%s-%03d" % (fam, i), build(fam, rng)))
    return out
