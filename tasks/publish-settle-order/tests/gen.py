"""Nonce programs, generated inside the verifier after the agent has finished.

Twelve families. Ten are small and shaped at the decisions that interact: which publisher
answers a name and who is allowed to see it, when a startup call resolves, what a released hold
takes down with it, whether a name that comes back is the unit that left, and what a call that
finds nothing brings up - where it lands in the order, whose scope it lands in, who keeps it up,
and what happens when that keeper goes. The other two are the scale families - one where the
order is long, almost all of it is invisible to any one caller, and every caller brings a unit
up in front of itself and takes it down again; one where a single release brings a forest of
dependencies down.

Nothing here depends on the shipped programs, so a submission fitted to those fails, and nothing
here can be seen before the run: the seed is drawn after the agent's container is gone.
"""
import random

FAMILIES = (("plain", 1), ("race", 1), ("cyc", 1), ("again", 1), ("casc", 1),
             ("soft", 1), ("scope", 1), ("deep", 1), ("lazy", 1), ("fan", 1),
             ("wide", 0), ("tear", 0))

WIDE_SYMS = 4
WIDE_DENS = 200
WIDE_PER_DEN = 200
WIDE_CALLERS = 5000

TEAR_UNITS = 24000
TEAR_FAN = 3


def _rng(seed, fam, i):
    return random.Random("%s:%s:%d" % (seed, fam, i))


def _decl(lines, units, autos=()):
    """Emit the declaration block for a list of (name, needs, pubs, boots) tuples.

    A need is (other, hard): a hard one keeps its target up, an ordering one only decides when
    the target comes up. `autos` are marked in the order given, which is the order a call
    considers them in.
    """
    for name, _n, _p, _b in units:
        lines.append("unit " + name)
    for name, needs, pubs, boots in units:
        for other, hard in needs:
            lines.append("%s %s %s" % ("dep" if hard else "pre", name, other))
        for sym, fall in pubs:
            lines.append("%s %s %s" % ("fall" if fall else "pub", name, sym))
        for sym in boots:
            lines.append("boot %s %s" % (name, sym))
    for name in autos:
        lines.append("auto " + name)


def _plain(r):
    n = r.randint(4, 9)
    m = r.randint(2, 4)
    syms = ["s%d" % i for i in range(m)]
    names = ["u%d" % i for i in range(n)]
    units = []
    for i, name in enumerate(names):
        deps = [(x, r.random() < 0.7)
                for x in (r.sample(names[:i], min(i, r.randint(0, 2))) if i else [])]
        pubs = [(r.choice(syms), r.random() < 0.3) for _ in range(r.randint(0, 2))]
        boots = [r.choice(syms)] if r.random() < 0.35 else []
        units.append((name, deps, pubs, boots))
    lines = []
    _decl(lines, units)
    held = []
    for _ in range(r.randint(8, 20)):
        k = r.random()
        if k < 0.4 or not held:
            u = r.choice(names)
            held.append(u)
            lines.append("act " + u)
        elif k < 0.8:
            lines.append("call %s %s" % (r.choice(names), r.choice(syms)))
        else:
            lines.append("rel " + held.pop(r.randrange(len(held))))
    return lines


def _race(r):
    syms = ["s0", "s1"]
    prov = ["p%d" % i for i in range(r.randint(3, 6))]
    call = ["c%d" % i for i in range(r.randint(2, 3))]
    units = []
    for name in prov:
        pubs = [(s, r.random() < 0.5) for s in syms if r.random() < 0.8]
        if not pubs:
            pubs = [(r.choice(syms), r.random() < 0.5)]
        units.append((name, [], pubs, []))
    for name in call:
        boots = [r.choice(syms)] if r.random() < 0.5 else []
        units.append((name, [], [], boots))
    lines = []
    _decl(lines, units)
    order = prov[:]
    r.shuffle(order)
    for name in order:
        lines.append("act " + name)
        if r.random() < 0.3:
            lines.append("call %s %s" % (r.choice(call), r.choice(syms)))
    for name in call:
        lines.append("act " + name)
    for _ in range(r.randint(4, 10)):
        k = r.random()
        if k < 0.55:
            lines.append("call %s %s" % (r.choice(call), r.choice(syms)))
        elif k < 0.8:
            lines.append("rel " + r.choice(order))
        else:
            lines.append("act " + r.choice(order))
    return lines


def _cyc(r):
    n = r.randint(3, 5)
    names = ["u%d" % i for i in range(n)]
    syms = ["s%d" % i for i in range(n)]
    units = []
    for i, name in enumerate(names):
        deps = [(names[(i + 1) % n], r.random() < 0.75)]
        if n > 3 and r.random() < 0.4:
            deps.append((names[(i + 2) % n], r.random() < 0.75))
        pubs = [(syms[i], r.random() < 0.3)]
        boots = [syms[(i + 1) % n]] if r.random() < 0.8 else []
        units.append((name, deps, pubs, boots))
    lines = []
    _decl(lines, units)
    lines.append("act " + names[r.randrange(n)])
    for _ in range(r.randint(3, 8)):
        k = r.random()
        if k < 0.6:
            lines.append("call %s %s" % (r.choice(names), r.choice(syms)))
        elif k < 0.85:
            lines.append("act " + r.choice(names))
        else:
            lines.append("rel " + r.choice(names))
    return lines


def _again(r):
    """Retire and return, with some providers brought up by the calls that need them."""
    syms = ["s%d" % i for i in range(r.randint(1, 2))]
    prov = ["p%d" % i for i in range(r.randint(2, 4))]
    call = ["c%d" % i for i in range(r.randint(1, 3))]
    units = []
    for name in prov:
        units.append((name, [], [(s, r.random() < 0.35) for s in syms], []))
    for name in call:
        units.append((name, [], [], []))
    autos = [p for p in prov if r.random() < 0.4]
    r.shuffle(autos)
    lines = []
    _decl(lines, units, autos)
    for name in call:
        lines.append("act " + name)
        if r.random() < 0.6:
            lines.append("call %s %s" % (name, r.choice(syms)))
    for name in prov:
        lines.append("act " + name)
    for name in call:
        for s in syms:
            lines.append("call %s %s" % (name, s))
    for _ in range(r.randint(2, 5)):
        who = r.choice(prov)
        lines.append("rel " + who)
        if r.random() < 0.8:
            lines.append("act " + who)
        if r.random() < 0.4:
            back = r.choice(call)
            lines.append("rel " + back)
            lines.append("act " + back)
        for name in call:
            for s in syms:
                if r.random() < 0.75:
                    lines.append("call %s %s" % (name, s))
    return lines


def _casc(r):
    leaf = ["l%d" % i for i in range(r.randint(2, 4))]
    mid = ["m%d" % i for i in range(r.randint(2, 3))]
    top = ["t%d" % i for i in range(r.randint(1, 2))]
    syms = ["s0", "s1"]
    units = []
    for name in leaf:
        units.append((name, [], [(r.choice(syms), r.random() < 0.4)], []))
    for name in mid:
        deps = [(x, r.random() < 0.75) for x in r.sample(leaf, r.randint(1, len(leaf)))]
        boots = [r.choice(syms)] if r.random() < 0.5 else []
        units.append((name, deps, [], boots))
    for name in top:
        deps = [(x, r.random() < 0.8) for x in r.sample(mid, r.randint(1, len(mid)))]
        units.append((name, deps, [], []))
    lines = []
    _decl(lines, units)
    for name in top:
        lines.append("act " + name)
    extra = r.sample(leaf + mid, r.randint(0, 2))
    for name in extra:
        lines.append("act " + name)
    for _ in range(r.randint(3, 7)):
        lines.append("call %s %s" % (r.choice(mid + top), r.choice(syms)))
    for name in top + extra:
        lines.append("rel " + name)
        if r.random() < 0.3:
            lines.append("call %s %s" % (r.choice(mid), r.choice(syms)))
    return lines


def _wide(r):
    """Long order, most of it invisible to any one caller, and every caller loading in front
    of itself.

    The public providers come up a quarter of the way through the callers, so for the first
    quarter the private publisher a caller brought up with it is the answer and for the rest the
    public one is: every call compares the heads of two buckets. Each caller then brings one `auto` unit
    up directly ahead of itself and gives its hold back, so the order is spliced into and out of
    once per caller, thousands of times, against twenty thousand publications that never move.
    """
    syms = ["s%d" % i for i in range(WIDE_SYMS)]
    lines = []
    churn = ["k%d" % i for i in range(20)]
    for name in churn:
        lines.append("unit " + name)
        lines.append("pub %s q%s" % (name, name))
    for name in churn:
        lines.append("act " + name)
    for _ in range(60):
        name = r.choice(churn)
        lines.append("rel " + name)
        lines.append("act " + name)
    for i in range(WIDE_SYMS):
        lines.append("unit a%d" % i)
        lines.append("pub a%d z%d" % (i, i))
        lines.append("auto a%d" % i)
    dens = int(WIDE_DENS * r.uniform(0.85, 1.15))
    for d in range(dens):
        head = "d%d" % d
        lines.append("unit " + head)
        for i in range(WIDE_PER_DEN):
            name = "d%d_%d" % (d, i)
            lines.append("unit " + name)
            lines.append("pub %s %s" % (name, syms[i % WIDE_SYMS]))
            lines.append("dep %s %s" % (head, name))
        lines.append("open " + head)
    prov = ["p%d" % i for i in range(WIDE_SYMS)]
    for i, name in enumerate(prov):
        lines.append("unit " + name)
        lines.append("pub %s %s" % (name, syms[i]))
    n = int(WIDE_CALLERS * r.uniform(0.85, 1.15))
    call = ["c%d" % i for i in range(n)]
    for i, name in enumerate(call):
        lines.append("unit " + name)
        lines.append("unit v%d" % i)
        lines.append("pub v%d %s" % (i, syms[i % WIDE_SYMS]))
        lines.append("dep %s v%d" % (name, i))
    for i, name in enumerate(call):
        if i == n // 4:
            for p in prov:
                lines.append("act " + p)
        lines.append("%s %s" % ("act" if i % 5 == 0 else "open", name))
        lines.append("call %s z%d" % (name, i % WIDE_SYMS))
        for sym in syms:
            lines.append("call %s %s" % (name, sym))
        lines.append("rel " + name)
    return lines


def _soft(r):
    names = ["u%d" % i for i in range(r.randint(3, 6))]
    syms = ["s%d" % i for i in range(r.randint(1, 3))]
    units = []
    for i, name in enumerate(names):
        needs = []
        for other in (r.sample(names[:i], min(i, r.randint(0, 2))) if i else []):
            needs.append((other, r.random() < 0.25))
        pubs = [(r.choice(syms), r.random() < 0.3)] if r.random() < 0.8 else []
        boots = [r.choice(syms)] if r.random() < 0.3 else []
        units.append((name, needs, pubs, boots))
    lines = []
    _decl(lines, units)
    holding = []
    for _ in range(r.randint(6, 16)):
        k = r.random()
        if k < 0.35 or not holding:
            who = r.choice(names)
            holding.append(who)
            lines.append("act " + who)
        elif k < 0.7:
            lines.append("call %s %s" % (r.choice(names), r.choice(syms)))
        else:
            lines.append("rel " + holding.pop(r.randrange(len(holding))))
    for who in holding:
        lines.append("rel " + who)
    return lines


def _scope(r):
    """Scopes, promotion, and loads captured by the scope of the caller that made them."""
    syms = ["s%d" % i for i in range(r.randint(1, 3))]
    prov = ["p%d" % i for i in range(r.randint(2, 5))]
    call = ["c%d" % i for i in range(r.randint(2, 4))]
    late = ["e%d" % i for i in range(2)]
    units = []
    for name in prov:
        units.append((name, [], [(r.choice(syms), r.random() < 0.3)], []))
    for name in call:
        needs = [(x, r.random() < 0.6) for x in r.sample(prov, r.randint(1, len(prov)))]
        boots = [r.choice(syms)] if r.random() < 0.35 else []
        units.append((name, needs, [], boots))
    for name in late:
        units.append((name, [], [], []))
    autos = [p for p in prov if r.random() < 0.5]
    lines = []
    _decl(lines, units, autos)
    for name in call:
        lines.append("%s %s" % ("open" if r.random() < 0.7 else "act", name))
        for sym in syms:
            if r.random() < 0.7:
                lines.append("call %s %s" % (name, sym))
    for name in r.sample(prov, r.randint(1, len(prov))):
        if r.random() < 0.7:
            lines.append("act " + name)
    for name in late:
        lines.append("%s %s" % ("act" if r.random() < 0.6 else "open", name))
        for sym in syms:
            lines.append("call %s %s" % (name, sym))
    for _ in range(r.randint(3, 8)):
        k = r.random()
        if k < 0.45:
            lines.append("call %s %s" % (r.choice(call + late), r.choice(syms)))
        elif k < 0.65:
            lines.append("act " + r.choice(prov))
        elif k < 0.8:
            lines.append("act " + r.choice(call + late))
        else:
            lines.append("rel " + r.choice(prov + call))
    return lines


def _deep(r):
    n = r.randint(6, 11)
    names = ["u%d" % i for i in range(n)]
    syms = ["s0", "s1"]
    units = []
    for i, name in enumerate(names):
        needs = []
        for other in (r.sample(names[:i], min(i, r.randint(0, 2))) if i else []):
            needs.append((other, r.random() < 0.7))
            if r.random() < 0.15:
                needs.append((other, True))
        if i and r.random() < 0.2:
            needs.append((names[i - 1], False))
        pubs = [(r.choice(syms), r.random() < 0.3)] if r.random() < 0.6 else []
        units.append((name, needs, pubs, []))
    lines = []
    _decl(lines, units)
    held = r.sample(names, r.randint(1, 3))
    for name in held:
        lines.append("act " + name)
    for _ in range(r.randint(2, 6)):
        lines.append("call %s %s" % (r.choice(names), r.choice(syms)))
    for name in held:
        lines.append("rel " + name)
        if r.random() < 0.4:
            lines.append("call %s %s" % (r.choice(names), r.choice(syms)))
    return lines


def _lazy(r):
    """Units brought up by calls: chains of them through startup calls, into scopes, kept by
    their callers and taken down with them, brought up again by the next call that needs them,
    and some declared only after the program has started."""
    m = r.randint(2, 4)
    syms = ["s%d" % i for i in range(m)]
    autos = ["a%d" % i for i in range(r.randint(2, 5))]
    prov = ["p%d" % i for i in range(r.randint(0, 2))]
    call = ["c%d" % i for i in range(r.randint(1, 3))]
    units = []
    for i, name in enumerate(autos):
        needs = []
        pool = autos[:i] + prov
        if pool and r.random() < 0.5:
            needs.append((r.choice(pool), r.random() < 0.6))
        pubs = [(r.choice(syms), r.random() < 0.3) for _ in range(r.randint(1, 2))]
        boots = [r.choice(syms) for _ in range(r.randint(0, 2))]
        units.append((name, needs, pubs, boots))
    for name in prov:
        units.append((name, [], [(r.choice(syms), r.random() < 0.3)], []))
    for name in call:
        needs = [(x, True) for x in prov if r.random() < 0.3]
        boots = [r.choice(syms)] if r.random() < 0.4 else []
        units.append((name, needs, [], boots))
    marks = autos[:]
    r.shuffle(marks)
    lines = []
    _decl(lines, units, marks)
    holding = []
    late = 0
    for _ in range(r.randint(8, 18)):
        k = r.random()
        if k < 0.25 or not holding:
            who = r.choice(call + prov)
            holding.append(who)
            lines.append("%s %s" % ("open" if r.random() < 0.4 else "act", who))
        elif k < 0.6:
            lines.append("call %s %s" % (r.choice(call + autos), r.choice(syms)))
        elif k < 0.72:
            lines.append("act " + r.choice(autos))
            holding.append(lines[-1][4:])
        elif k < 0.88:
            lines.append("rel " + holding.pop(r.randrange(len(holding))))
        elif late < 2:
            late += 1
            name = "n%d" % late
            lines.append("unit " + name)
            lines.append("pub %s %s" % (name, r.choice(syms)))
            if r.random() < 0.5:
                lines.append("boot %s %s" % (name, r.choice(syms)))
            lines.append("auto " + name)
            autos.append(name)
        else:
            lines.append("call %s %s" % (r.choice(call), r.choice(syms)))
    if r.random() < 0.8:
        # a provider comes up in a scope of its own after a fresh caller, invisible to it; the
        # caller's call loads a unit directly ahead of itself; then the provider is made public
        # and a third unit asks. The load sits ahead of the provider in the order and after it
        # in time, so this is where a serial and a place disagree.
        sym = r.choice(syms)
        lines.append("unit g")
        lines.append("act g")
        lines.append("unit q")
        lines.append("pub q %s" % sym)
        lines.append("open q")
        lines.append("call g %s" % sym)
        lines.append("act q")
        lines.append("unit x")
        lines.append("%s x" % ("open" if r.random() < 0.3 else "act"))
        lines.append("call x %s" % sym)
        for who in autos:
            if r.random() < 0.3:
                lines.append("act " + who)
        lines.append("call x %s" % r.choice(syms))
        holding.append("g")
        if r.random() < 0.5:
            lines.append("rel g")
            holding.remove("g")
            lines.append("call x %s" % sym)
    if r.random() < 0.5:
        # a caller brought up in a scope and then made public still loads into its own scope
        lines.append("unit y")
        lines.append("unit w")
        lines.append("open y")
        lines.append("act y")
        for sym in r.sample(syms, min(len(syms), 2)):
            lines.append("call y %s" % sym)
        lines.append("act w")
        for sym in syms:
            lines.append("call w %s" % sym)
        holding.append("y")
        holding.append("w")
    for who in holding:
        lines.append("rel " + who)
        if r.random() < 0.3:
            lines.append("call %s %s" % (r.choice(call), r.choice(syms)))
    return lines


def _fan(r):
    """One caller bringing up many units in front of itself, then taking them all down and
    doing it again.

    Every load lands between the previous load and the caller, so this is the family that
    tells an order key that admits unbounded insertion from one that only looks as if it did.
    """
    n = r.randint(55, 80)
    syms = ["z%d" % i for i in range(n)]
    units = [("a%d" % i, [], [(syms[i], r.random() < 0.2)], []) for i in range(n)]
    units.append(("c", [], [], []))
    units.append(("d", [], [], []))
    units.append(("p", [], [(syms[n - 1], False), (syms[0], False)], []))
    marks = ["a%d" % i for i in range(n)]
    r.shuffle(marks)
    lines = []
    _decl(lines, units, marks)
    order = list(range(n))
    r.shuffle(order)
    for life in range(2):
        lines.append("%s c" % ("open" if r.random() < 0.3 else "act"))
        if life == 0:
            lines.append("open p")
        for i in order:
            lines.append("call c %s" % syms[i])
        if life == 0:
            lines.append("act p")
            lines.append("act d")
        for i in r.sample(order, 4):
            lines.append("call d %s" % syms[i])
        lines.append("call d %s" % syms[n - 1])
        lines.append("call d %s" % syms[0])
        lines.append("rel c")
        for i in r.sample(order, 2):
            lines.append("call d %s" % syms[i])
    return lines


def _tear(r):
    """One release brings down a forest, which is where a rescanning sweep dies."""
    n = int(TEAR_UNITS * r.uniform(0.85, 1.15))
    lines = ["unit t0"]
    for i in range(1, n):
        lines.append("unit t%d" % i)
        lines.append("dep t%d t%d" % ((i - 1) // TEAR_FAN, i))
    stray = ["k%d" % i for i in range(30)]
    for name in stray:
        lines.append("unit " + name)
        lines.append("pre %s t%d" % (name, r.randrange(n)))
    lines.append("act t0")
    for name in stray:
        lines.append("act " + name)
    for name in stray:
        lines.append("rel " + name)
    lines.append("rel t0")
    return lines


BUILD = {"plain": _plain, "race": _race, "cyc": _cyc, "again": _again,
         "casc": _casc, "soft": _soft, "scope": _scope, "deep": _deep,
         "lazy": _lazy, "fan": _fan, "wide": _wide, "tear": _tear}


def programs(seed, per):
    """Every graded nonce program, as (family, name, lines)."""
    out = []
    for fam, small in FAMILIES:
        n = per if small else max(2, per // 15)
        for i in range(n):
            out.append((fam, "%s-%03d" % (fam, i), BUILD[fam](_rng(seed, fam, i))))
    return out


def ops(lines):
    return list(lines)
