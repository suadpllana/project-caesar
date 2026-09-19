"""Step files generated from a seed drawn after the agent's container is gone.

The families are shaped around the decisions rather than sampled from the input space: an
unshaped population puts almost no pressure on the buffers, so displacement never happens, the
deferral queue stays empty and every wrong reading scores the same as the right one. Each
family below concentrates one mechanism, and the two scale families exist for the execution
limit rather than for a rule.

  plain    ordinary steps: some pressure, some spare room, nothing concentrated
  tight    buffers barely big enough, so nearly every rank-zero arrival has to displace
  uneven   a first microbatch whose wanted slots are nothing like the rest of the step
  chain    tokens holding three or four ranks meeting a much stronger arrival at rank zero
  strike   top scores just under the threshold, so striking one out lengthens the want list
  shedy    a small bank share, with want lists that reach across bank boundaries
  lastmb   the pressure held back until the last microbatch, where a loss is held not queued
  flat     equal scores everywhere, for the three tie-breaks
  low      whole rankings that fall short of the threshold
  wide     one long step, many tokens, large buffers
  deep     many microbatches, long want lists, repeated deferral
"""
import random

FAMILIES = (
    ("plain", False),
    ("tight", False),
    ("uneven", False),
    ("chain", False),
    ("strike", False),
    ("shedy", False),
    ("lastmb", False),
    ("flat", False),
    ("low", False),
    ("wide", True),
    ("deep", True),
)

BIG = 3


def _sharp(rng, ex, w):
    """One expert over the threshold on its own: a want list of length one."""
    sc = [rng.randint(0, 40) for _ in range(ex)]
    sc[rng.randrange(ex)] = w + rng.randint(0, 200)
    return sc


def _flat(rng, ex, w):
    """Near-equal scores: a long want list."""
    base = max(1, w // max(2, ex - 1))
    return [max(0, base + rng.randint(-base // 3, base // 3)) for _ in range(ex)]


def _near(rng, ex, w):
    """A top score just short of the threshold, with small scores behind it."""
    sc = [rng.randint(1, 25) for _ in range(ex)]
    sc[rng.randrange(ex)] = max(1, w - rng.randint(1, 40))
    return sc


def _tied(rng, ex, w):
    v = rng.choice([90, 140, 210])
    return [v if rng.random() < 0.75 else v + rng.choice([-v // 3, v // 3]) for _ in range(ex)]


def _small(rng, ex, w):
    top = max(1, w // (ex * 2))
    return [rng.randint(0, top) for _ in range(ex)]


def _pick(rng, ex, w, kinds):
    return rng.choice(kinds)(rng, ex, w)


def _tok(sc):
    return "t " + " ".join(str(x) for x in sc)


def _head(rng, ex=None, bw=None, w=None, f=None, g=None):
    if ex is None:
        ex = rng.choice([4, 6, 8, 12])
    if bw is None:
        bw = rng.choice([d for d in (2, 3, 4) if ex % d == 0])
    if w is None:
        w = rng.choice([350, 450, 600, 750])
    if f is None:
        f = rng.choice([80, 100, 130, 160])
    if g is None:
        g = rng.choice([55, 70, 85])
    return ["cfg %d %d %d %d %d" % (ex, bw, w, f, g)], ex, bw, w, f, g


def _steps(lines, groups):
    lines.append("step")
    for group in groups:
        lines.append("mb")
        for sc in group:
            lines.append(_tok(sc))


def build(fam, rng):
    if fam == "plain":
        lines, ex, _bw, w, _f, _g = _head(rng)
        for _ in range(rng.randint(1, 2)):
            groups = []
            for _m in range(rng.randint(1, 3)):
                groups.append([_pick(rng, ex, w, (_sharp, _flat, _near))
                               for _ in range(rng.randint(3, 9))])
            _steps(lines, groups)
        return lines

    if fam == "tight":
        lines, ex, _bw, w, _f, _g = _head(rng, f=rng.choice([35, 45, 60]))
        groups = []
        for _m in range(rng.randint(2, 3)):
            groups.append([_pick(rng, ex, w, (_sharp, _near))
                           for _ in range(rng.randint(5, 11))])
        _steps(lines, groups)
        return lines

    if fam == "uneven":
        lines, ex, _bw, w, _f, _g = _head(rng, f=rng.choice([60, 90, 120]))
        thin = rng.random() < 0.5
        head = [_sharp(rng, ex, w) for _ in range(rng.randint(2, 4))] if thin else \
               [_flat(rng, ex, w) for _ in range(rng.randint(7, 11))]
        groups = [head]
        for _m in range(rng.randint(2, 3)):
            groups.append([_pick(rng, ex, w, (_flat, _near) if thin else (_sharp,))
                           for _ in range(rng.randint(5, 10))])
        _steps(lines, groups)
        return lines

    if fam == "chain":
        lines, ex, _bw, w, _f, _g = _head(rng, w=rng.choice([600, 750]),
                                          f=rng.choice([40, 55, 70]))
        groups = [[_flat(rng, ex, w) for _ in range(rng.randint(4, 8))]]
        for _m in range(rng.randint(1, 3)):
            group = []
            for _ in range(rng.randint(4, 8)):
                sc = _sharp(rng, ex, w)
                sc[sc.index(max(sc))] = w + 400 + rng.randint(0, 300)
                group.append(sc)
            group.extend(_flat(rng, ex, w) for _ in range(rng.randint(1, 3)))
            rng.shuffle(group)
            groups.append(group)
        _steps(lines, groups)
        return lines

    if fam == "strike":
        lines, ex, _bw, w, _f, _g = _head(rng, w=rng.choice([450, 600]),
                                          f=rng.choice([30, 40, 55]))
        groups = []
        for _m in range(rng.randint(2, 4)):
            groups.append([_near(rng, ex, w) for _ in range(rng.randint(4, 9))])
        _steps(lines, groups)
        return lines

    if fam == "shedy":
        lines, ex, _bw, w, _f, _g = _head(rng, ex=rng.choice([6, 8, 12]), bw=2,
                                          g=rng.choice([25, 35, 50]),
                                          f=rng.choice([110, 150]))
        groups = []
        for _m in range(rng.randint(1, 3)):
            groups.append([_pick(rng, ex, w, (_flat, _near))
                           for _ in range(rng.randint(5, 10))])
        _steps(lines, groups)
        return lines

    if fam == "lastmb":
        lines, ex, _bw, w, _f, _g = _head(rng, f=rng.choice([45, 60]))
        groups = [[_sharp(rng, ex, w) for _ in range(rng.randint(2, 4))]]
        for _m in range(rng.randint(1, 2)):
            groups.append([_sharp(rng, ex, w) for _ in range(rng.randint(2, 4))])
        groups.append([_flat(rng, ex, w) for _ in range(rng.randint(7, 12))])
        _steps(lines, groups)
        return lines

    if fam == "flat":
        lines, ex, _bw, w, _f, _g = _head(rng, w=rng.choice([350, 450]),
                                          f=rng.choice([45, 60, 80]))
        groups = []
        for _m in range(rng.randint(2, 3)):
            groups.append([_tied(rng, ex, w) for _ in range(rng.randint(5, 10))])
        _steps(lines, groups)
        return lines

    if fam == "low":
        lines, ex, _bw, w, _f, _g = _head(rng, w=rng.choice([600, 900]),
                                          f=rng.choice([40, 60, 90]))
        groups = []
        for _m in range(rng.randint(1, 3)):
            groups.append([_pick(rng, ex, w, (_small, _flat))
                           for _ in range(rng.randint(4, 9))])
        _steps(lines, groups)
        return lines

    if fam == "wide":
        lines, ex, _bw, w, _f, _g = _head(rng, ex=8, bw=4, w=600, f=70,
                                          g=rng.choice([70, 85]))
        groups = []
        for m in range(4):
            group = []
            for _ in range(7000):
                group.append(_near(rng, ex, w) if rng.random() < 0.55
                             else _sharp(rng, ex, w))
            groups.append(group)
        _steps(lines, groups)
        return lines

    if fam == "deep":
        lines, ex, _bw, w, _f, _g = _head(rng, ex=12, bw=3, w=750, f=45,
                                          g=rng.choice([60, 80]))
        groups = []
        for m in range(9):
            group = []
            for _ in range(2400):
                group.append(_flat(rng, ex, w) if rng.random() < 0.6
                             else _near(rng, ex, w))
            groups.append(group)
        _steps(lines, groups)
        return lines

    raise AssertionError("unknown family %s" % fam)


def programs(seed, per):
    """Every graded program for this run, as (family, name, lines)."""
    out = []
    for fam, big in FAMILIES:
        count = BIG if big else per
        for i in range(count):
            rng = random.Random("%s|%s|%d" % (seed, fam, i))
            out.append((fam, "%s-%03d" % (fam, i), build(fam, rng)))
    return out
