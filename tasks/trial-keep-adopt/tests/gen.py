"""The graded population, built from a seed the submission never saw.

Twelve families. Nine are small and shaped around one mechanism each, because an unshaped
population does not exercise the mechanism it is supposed to (a wrong reading that moves 3.7% of
random programs moves 42% of a shaped one). Two are the scale families the execution limit exists
for. One is unshaped, to keep the population honest about ordinary programs.

  plain   random definitions, publications and questions
  cut     caps under moving sources, so a source moves without moving the field above it
  flip    branch guards that flip, so a field stops reading the arm it read last time
  bail    long read lists whose first difference sits early, with expensive fields behind it
  pre     preview blocks that end, then questions in the base world
  adopt   preview blocks whose value is then published
  stale   preview, an unrelated publication that moves a read, then the previewed value
  other   preview discarded by a different value, by another preview, or left standing
  pinned  pins and frees across publications and previews
  same    publications repeating the value a source already carries
  wide    many independent chains with a preview over each
  deep    a ladder of diamonds asked repeatedly
"""
import random

FAMILIES = (
    ("plain", False),
    ("cut", False),
    ("flip", False),
    ("bail", False),
    ("pre", False),
    ("adopt", False),
    ("stale", False),
    ("other", False),
    ("pinned", False),
    ("same", False),
    ("wide", True),
    ("deep", True),
)

BIG = 3


def build(rnd, nsrc, nder, forms, cap_lo=1, cap_hi=40):
    """A random acyclic field graph: sources first, then derived fields over earlier names."""
    lines, src, der = [], [], []
    for i in range(nsrc):
        n = "s%d" % i
        lines.append("def %s raw" % n)
        src.append(n)
    for i in range(nder):
        n = "d%d" % i
        pool = src + der
        kind = rnd.choice(forms)
        if kind == "sum":
            k = rnd.randint(2, min(4, len(pool)) if len(pool) > 1 else 2)
            args = [rnd.choice(pool) for _ in range(k)]
        elif kind == "cap":
            args = [rnd.choice(pool), str(rnd.randint(cap_lo, cap_hi))]
        elif kind == "pick":
            args = [rnd.choice(pool), rnd.choice(pool), rnd.choice(pool)]
        else:
            args = [rnd.choice(pool), rnd.choice(pool)]
        lines.append("def %s %s %s" % (n, kind, " ".join(args)))
        der.append(n)
    return lines, src, der


def sets(rnd, src, n, hi=9):
    return ["set %s %d" % (rnd.choice(src), rnd.randint(0, hi)) for _ in range(n)]


def plain(rnd):
    lines, src, der = build(rnd, rnd.randint(2, 4), rnd.randint(4, 9),
                            ["sum", "cap", "pick", "gate"])
    for _ in range(rnd.randint(6, 14)):
        if rnd.random() < 0.45:
            lines += sets(rnd, src, 1)
        else:
            lines.append("ask %s" % rnd.choice(der))
    return lines


def cut(rnd):
    lines, src, der = build(rnd, 2, rnd.randint(4, 8), ["cap", "sum"], 1, 4)
    for _ in range(rnd.randint(8, 16)):
        if rnd.random() < 0.5:
            lines += sets(rnd, src, 1, 12)
        else:
            lines.append("ask %s" % rnd.choice(der))
    return lines


def rig(rnd, arms=2):
    """A guard over two arms, each a chain over its own source, with a field above the pick.

    This is the shape every rule about read lists needs: the guard decides which arm is in the
    record, and the abandoned arm keeps a source of its own that can move behind its back.
    """
    lines = ["def g raw", "def z raw"]
    src = ["g", "z"]
    tops = []
    for j in range(arms):
        s = "s%d" % j
        lines.append("def %s raw" % s)
        src.append(s)
        lines.append("def m%d cap %s %d" % (j, s, rnd.randint(3, 20)))
        lines.append("def n%d sum m%d m%d" % (j, j, j))
        tops.append("n%d" % j)
    der = ["m%d" % j for j in range(arms)] + tops
    if rnd.random() < 0.65:
        lines.append("def w pick g %s %s" % (tops[0], tops[-1]))
    else:
        lines.append("def w gate g %s" % tops[0])
    lines.append("def t sum w z")
    der += ["w", "t"]
    return lines, src, der, tops


def flip(rnd):
    """Guards that flip, then publications under the arm the field has stopped reading."""
    lines, src, der, _tops = rig(rnd, 2)
    lines += ["set g %d" % rnd.randint(1, 4), "set s0 %d" % rnd.randint(1, 9),
              "set s1 %d" % rnd.randint(1, 9), "set z %d" % rnd.randint(0, 5)]
    lines.append("ask %s" % rnd.choice(["w", "t"]))
    for _ in range(rnd.randint(3, 6)):
        roll = rnd.random()
        if roll < 0.3:
            lines.append("set g %d" % rnd.choice([0, 0, 1, 3]))
        elif roll < 0.7:
            lines.append("set s%d %d" % (rnd.randint(0, 1), rnd.randint(0, 40)))
        else:
            lines.append("set z %d" % rnd.randint(0, 5))
        lines.append("ask %s" % rnd.choice(["w", "t", "w"]))
    lines.append("ask %s" % rnd.choice(der))
    return lines


def bail(rnd):
    """The abandoned arm left stale at the moment the guard flips.

    A check that walks past the first read that differs demands that arm, and the arm evaluates:
    work the coming evaluation was never going to ask for.
    """
    lines, src, der, _tops = rig(rnd, 2)
    lines += ["set g 1", "set s0 %d" % rnd.randint(1, 9), "set s1 %d" % rnd.randint(1, 9),
              "set z %d" % rnd.randint(0, 5), "ask t"]
    for r in range(rnd.randint(2, 4)):
        lines.append("set s%d %d" % (r % 2, rnd.randint(10, 60)))
        lines.append("set g %d" % (0 if r % 2 == 0 else rnd.randint(1, 4)))
        lines.append("ask %s" % rnd.choice(["t", "w"]))
        if rnd.random() < 0.5:
            lines.append("set s%d %d" % ((r + 1) % 2, rnd.randint(0, 9)))
            lines.append("ask t")
    return lines


def pinned(rnd):
    """Pins over a source that then moves, and a pin taken before anything was evaluated.

    The core of every program here is the shape that separates a pin from a check: pin a field,
    move the source under it, then ask a field above it. A service that checks a pinned field
    evaluates the chain under it and then the field itself, and the pin is worth nothing.
    """
    lines, src, der, _tops = rig(rnd, 2)
    lines += ["set g %d" % rnd.randint(1, 3), "set s0 %d" % rnd.randint(1, 9),
              "set s1 %d" % rnd.randint(1, 9), "set z %d" % rnd.randint(0, 4), "ask t"]
    for r in range(rnd.randint(2, 4)):
        arm = rnd.choice([0, 1])
        held = rnd.choice(["m%d" % arm, "n%d" % arm, "w"])
        lines.append("pin %s" % held)
        lines.append("set s%d %d" % (arm, rnd.randint(10, 60)))
        lines.append("ask %s" % rnd.choice(["t", "t", "w"]))
        if rnd.random() < 0.4:
            lines += ["try s%d %d" % (arm, rnd.randint(0, 30)), "ask t", "end"]
        if rnd.random() < 0.3:
            lines.append("set g %d" % rnd.choice([0, 1, 2]))
            lines.append("ask t")
        lines.append("free %s" % held)
        lines.append("ask %s" % rnd.choice(["t", "w"]))
    if rnd.random() < 0.6:
        lines += ["def fresh cap s0 %d" % rnd.randint(2, 30), "pin fresh", "ask fresh"]
    return lines


def block(rnd, src, der, val=None):
    s = rnd.choice(src)
    v = rnd.randint(0, 9) if val is None else val
    return s, v, ["try %s %d" % (s, v)] + ["ask %s" % rnd.choice(der)
                                           for _ in range(rnd.randint(1, 3))] + ["end"]


def pre(rnd):
    lines, src, der = build(rnd, 2, rnd.randint(4, 7), ["sum", "cap", "pick", "gate"], 1, 9)
    lines += sets(rnd, src, 2)
    lines += ["ask %s" % rnd.choice(der) for _ in range(2)]
    for _ in range(rnd.randint(2, 4)):
        _s, _v, blk = block(rnd, src, der)
        lines += blk
        lines += ["ask %s" % rnd.choice(der) for _ in range(rnd.randint(1, 2))]
    return lines


def adopt(rnd):
    lines, src, der = build(rnd, 2, rnd.randint(4, 7), ["sum", "cap", "pick", "gate"], 1, 9)
    lines += sets(rnd, src, 2)
    lines += ["ask %s" % rnd.choice(der) for _ in range(2)]
    for _ in range(rnd.randint(2, 3)):
        s, v, blk = block(rnd, src, der)
        lines += blk
        lines.append("set %s %d" % (s, v))
        lines += ["ask %s" % rnd.choice(der) for _ in range(rnd.randint(1, 3))]
    return lines


def stale(rnd):
    lines, src, der = build(rnd, 3, rnd.randint(4, 7), ["sum", "cap", "pick", "gate"], 1, 9)
    lines += sets(rnd, src, 3)
    lines += ["ask %s" % d for d in der]
    for _ in range(rnd.randint(2, 3)):
        s, v, blk = block(rnd, src, der)
        lines += blk
        other = [o for o in src if o != s]
        if other:
            lines.append("set %s %d" % (rnd.choice(other), rnd.randint(0, 9)))
        lines.append("set %s %d" % (s, v))
        lines += ["ask %s" % rnd.choice(der) for _ in range(rnd.randint(1, 3))]
    return lines


def other(rnd):
    """Layers thrown away: by a different value, by another block, and by nothing at all.

    Each block asks a field that has never been asked outside one, so a layer installed when it
    should have been discarded stands out: the field keeps a result it was never entitled to.
    """
    lines, src, der = build(rnd, 3, rnd.randint(3, 5), ["sum", "cap", "pick", "gate"], 1, 9)
    lines.append("def only sum %s %s" % (rnd.choice(der), rnd.choice(src)))
    lines.append("def also cap %s %d" % (rnd.choice(der), rnd.randint(2, 20)))
    lines += sets(rnd, src, 3)
    lines += ["ask %s" % rnd.choice(der) for _ in range(2)]
    for _ in range(rnd.randint(2, 4)):
        s = rnd.choice(src)
        v = rnd.randint(0, 9)
        held = rnd.choice(["only", "also"])
        lines += ["try %s %d" % (s, v), "ask %s" % held, "end"]
        roll = rnd.random()
        if roll < 0.55:
            lines.append("set %s %d" % (s, v + rnd.randint(1, 5)))
        elif roll < 0.75:
            s2 = rnd.choice(src)
            lines += ["try %s %d" % (s2, rnd.randint(0, 9)), "ask %s" % rnd.choice(der), "end"]
        else:
            lines.append("set %s %d" % (s, v))
        lines.append("ask %s" % held)
        lines += ["ask %s" % rnd.choice(["only", "also"] + der) for _ in range(rnd.randint(0, 2))]
    return lines


def same(rnd):
    lines, src, der = build(rnd, 2, rnd.randint(4, 7), ["sum", "cap", "pick", "gate"], 1, 9)
    held = {s: 0 for s in src}
    for _ in range(rnd.randint(10, 18)):
        roll = rnd.random()
        if roll < 0.3:
            s = rnd.choice(src)
            lines.append("set %s %d" % (s, held[s]))
        elif roll < 0.5:
            s = rnd.choice(src)
            held[s] = rnd.randint(0, 9)
            lines.append("set %s %d" % (s, held[s]))
        elif roll < 0.65:
            s = rnd.choice(src)
            lines += ["try %s %d" % (s, held[s]), "ask %s" % rnd.choice(der), "end",
                      "set %s %d" % (s, held[s])]
        else:
            lines.append("ask %s" % rnd.choice(der))
    return lines


def wide(rnd, n=20000, tries=20000):
    """Twenty thousand chains, and a preview opened over one of them at a time.

    Nothing a block does can reach more than the three fields of its own chain, so a layer that
    costs the size of the kept results costs twenty thousand times what it needed to.
    """
    lines = ["bulk W %d 97" % n]
    order = list(range(n))
    rnd.shuffle(order)
    lines += ["ask Wc%d" % i for i in order]
    step = rnd.choice([7919, 6151, 4441])
    for j in range(tries):
        i = (j * step) % n
        lines += ["try Wa%d %d" % (i, 500 + rnd.randint(0, 400)), "ask Wc%d" % i, "end"]
    return lines


def deep(rnd, k=30, rounds=2000):
    """A ladder of diamonds: every rung is read twice by the rung above it.

    A field settled once per question costs the height of the ladder; a field settled every time
    it is reached costs two to the power of it.
    """
    lines = ["def d0 raw"]
    for i in range(1, k + 1):
        lines.append("def a%d cap d%d 1000000000000" % (i, i - 1))
        lines.append("def b%d cap d%d 1000000000000" % (i, i - 1))
        lines.append("def d%d sum a%d b%d" % (i, i, i))
    top = "d%d" % k
    for _ in range(rounds):
        lines.append("set d0 %d" % rnd.randint(1, 500))
        lines.append("ask %s" % top)
        lines.append("ask %s" % top)
        if rnd.random() < 0.2:
            lines.append("ask a%d" % rnd.randint(1, k))
    return lines


MAKERS = {
    "plain": plain, "cut": cut, "flip": flip, "bail": bail, "pre": pre, "adopt": adopt,
    "stale": stale, "other": other, "pinned": pinned, "same": same,
}


def programs(seed, per):
    """(family, name, lines) for every graded program, in a fixed order."""
    out = []
    for fam, big in FAMILIES:
        n = BIG if big else per
        for i in range(n):
            rnd = random.Random("%s|%s|%d" % (seed, fam, i))
            if fam == "wide":
                lines = wide(rnd, 20000, 20000)
            elif fam == "deep":
                lines = deep(rnd, 30, 2000)
            else:
                lines = MAKERS[fam](rnd)
            out.append((fam, "%s-%d" % (fam, i), lines))
    return out


def one(fam, seed):
    """One program of a small family, for the authoring reading sweep."""
    return MAKERS[fam](random.Random(seed))
