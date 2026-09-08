"""Nonce programs, generated inside the verifier after the agent has finished.

Six families. Five are small and shaped at the decisions that interact: which publisher answers
a name, when a startup call resolves, what a released hold takes down with it, and whether a
name that comes back is the unit that left. The sixth is the scale family, where the order is
long and the publishers sit at the far end of it.

Nothing here depends on the shipped programs, so a submission fitted to those fails, and nothing
here can be seen before the run: the seed is drawn after the agent's container is gone.
"""
import random

FAMILIES = (("plain", 1), ("race", 1), ("cyc", 1), ("again", 1), ("casc", 1),
             ("soft", 1), ("wide", 0))

WIDE_FILL = 18000
WIDE_PUBS = 3
WIDE_SYMS = 50
WIDE_CALLERS = 1500


def _rng(seed, fam, i):
    return random.Random("%s:%s:%d" % (seed, fam, i))


def _decl(lines, units):
    """Emit the declaration block for a list of (name, needs, pubs, boots) tuples.

    A need is (other, hard): a hard one keeps its target up, an ordering one only decides when
    the target comes up.
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
    syms = ["s%d" % i for i in range(r.randint(1, 2))]
    prov = ["p%d" % i for i in range(r.randint(2, 4))]
    call = ["c%d" % i for i in range(r.randint(1, 3))]
    units = []
    for name in prov:
        units.append((name, [], [(s, r.random() < 0.35) for s in syms], []))
    for name in call:
        units.append((name, [], [], []))
    lines = []
    _decl(lines, units)
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
    syms = ["s%d" % i for i in range(WIDE_SYMS)]
    lines = []
    churn = ["k%d" % i for i in range(20)]
    for name in churn:
        lines.append("unit " + name)
        lines.append("pub %s %s" % (name, r.choice(syms)))
    for name in churn:
        lines.append("act " + name)
    for _ in range(60):
        name = r.choice(churn)
        lines.append("rel " + name)
        lines.append("act " + name)
    fill = ["f%d" % i for i in range(int(WIDE_FILL * r.uniform(0.85, 1.15)))]
    for i, name in enumerate(fill):
        lines.append("unit " + name)
        for j in range(WIDE_PUBS):
            lines.append("pub %s g%d" % (name, i * WIDE_PUBS + j))
    for name in fill:
        lines.append("act " + name)
    prov = ["p%d" % i for i in range(4)]
    for i, name in enumerate(prov):
        lines.append("unit " + name)
        for s in syms[i::4]:
            lines.append("pub %s %s" % (name, s))
    for name in prov:
        lines.append("act " + name)
    call = ["c%d" % i for i in range(int(WIDE_CALLERS * r.uniform(0.85, 1.15)))]
    for name in call:
        lines.append("unit " + name)
    for name in call:
        lines.append("act " + name)
    for name in call:
        for s in syms:
            lines.append("call %s %s" % (name, s))
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


BUILD = {"plain": _plain, "race": _race, "cyc": _cyc, "again": _again,
         "casc": _casc, "soft": _soft, "wide": _wide}


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
