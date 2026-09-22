"""The graded population, generated from a seed drawn after the agent's container is gone.

Eleven families. Nine concentrate one decision each - a closure that must refuse a live
candidate, an eviction that must give a span back, two members sharing one, two best
candidates on one token, a prompt that already carries the span, the two sides of the reach
bound, equal scores everywhere, and a search that runs out. Two are scale: one long search,
and one whose kept set turns over on nearly every step.
"""
import random

FAMILIES = [
    ("plain", False),
    ("lend", False),
    ("back", False),
    ("share", False),
    ("clash", False),
    ("pre", False),
    ("reach", False),
    ("tie", False),
    ("dry", False),
    ("wide", True),
    ("churn", True),
]
BIG = 3


def _edges(rng, v, deg, smax):
    """A scoring row for each of `deg` continuations of every context token."""
    out = []
    for a in range(1, v):
        pick = rng.sample(range(1, v), min(deg, v - 1))
        for b in pick:
            out.append((a, b, rng.randint(1, smax)))
    return out


def _stops(rng, v, how, smax):
    return [(a, 0, rng.randint(1, smax)) for a in sorted(rng.sample(range(1, v), how))]


def _text(cfg, rows, asks, rng):
    lines = ["cfg %d %d %d %d %d %d" % cfg]
    rows = list(rows)
    rng.shuffle(rows)
    lines += ["sc %d %d %d" % row for row in rows]
    lines += ["ask %s%s" % (name, "".join(" %d" % x for x in toks)) for name, toks in asks]
    return lines


def _prompts(rng, v, how, lo, hi):
    return [("q%d" % i, [rng.randint(1, v - 1) for _ in range(rng.randint(lo, hi))])
            for i in range(how)]


def make(fam, rng):
    if fam == "plain":
        v = rng.randint(4, 8)
        cfg = (rng.randint(2, 4), rng.randint(2, 3), rng.randint(1, 3),
               rng.randint(0, 3), rng.randint(1, 3), rng.randint(6, 16))
        rows = _edges(rng, v, rng.randint(2, 4), 9) + _stops(rng, v, max(1, (v - 1) // 2), 9)
        return _text(cfg, rows, _prompts(rng, v, rng.randint(1, 3), 1, 3), rng)

    if fam == "lend":
        # Stop edges everywhere and a low floor, so a closure lands on nearly every step and
        # the spans it lends have to refuse the candidates of that same step.
        v = rng.randint(4, 6)
        cfg = (rng.randint(2, 3), 2, 1, rng.randint(0, 2), rng.randint(2, 4), rng.randint(6, 14))
        rows = _edges(rng, v, rng.randint(2, 3), 6) + _stops(rng, v, v - 1, 6)
        return _text(cfg, rows, _prompts(rng, v, rng.randint(1, 3), 1, 2), rng)

    if fam == "back":
        # A kept set of one or two that turns over, so bans have to come back with the member.
        v = rng.randint(4, 7)
        cfg = (rng.randint(2, 4), 2, 1, rng.randint(0, 1), rng.randint(1, 2), rng.randint(8, 18))
        rows = _edges(rng, v, rng.randint(3, 4), 9) + _stops(rng, v, v - 1, 9)
        return _text(cfg, rows, _prompts(rng, v, rng.randint(1, 3), 1, 2), rng)

    if fam == "share":
        # Three tokens and a long prompt, so members overlap and one leaving must not free a
        # span another still holds.
        v = 4
        cfg = (rng.randint(2, 3), 2, 1, rng.randint(0, 2), rng.randint(2, 3), rng.randint(8, 16))
        rows = _edges(rng, v, 3, 5) + _stops(rng, v, 3, 5)
        return _text(cfg, rows, _prompts(rng, v, rng.randint(2, 3), 2, 5), rng)

    if fam == "clash":
        # Every context scores the same few tokens highest, so the best candidates of a step
        # collide on one token and selection has to walk past them.
        v = rng.randint(5, 8)
        hot = rng.sample(range(1, v), 2)
        rows = []
        for a in range(1, v):
            for b in sorted(set(hot + rng.sample(range(1, v), 2))):
                rows.append((a, b, 9 if b in hot else rng.randint(1, 4)))
        rows += _stops(rng, v, max(1, v // 2), 6)
        cfg = (rng.randint(2, 4), rng.randint(2, 3), rng.randint(1, 2),
               rng.randint(0, 2), rng.randint(1, 3), rng.randint(6, 14))
        return _text(cfg, rows, _prompts(rng, v, rng.randint(1, 3), 1, 3), rng)

    if fam == "pre":
        # Long prompts over few tokens, so the span a candidate would add is often already in
        # the prompt rather than in anything the search emitted.
        v = rng.randint(3, 5)
        cfg = (rng.randint(2, 3), rng.randint(2, 4), rng.randint(1, 2),
               rng.randint(0, 2), rng.randint(1, 3), rng.randint(6, 14))
        rows = _edges(rng, v, v - 1, 7) + _stops(rng, v, max(1, v - 2), 7)
        return _text(cfg, rows, _prompts(rng, v, rng.randint(1, 3), 5, 10), rng)

    if fam == "reach":
        # Penalties on both sides of the largest table score, with a ceiling far enough out
        # that the bound rather than the ceiling ends the search.
        v = rng.randint(4, 7)
        smax = rng.randint(3, 8)
        pen = rng.choice([0, 1, smax - 1, smax, smax + 1, smax + 2, smax + 4, smax + 7])
        cfg = (rng.randint(2, 3), 2, 1, max(0, pen), rng.randint(1, 2), rng.randint(20, 40))
        rows = _edges(rng, v, rng.randint(2, 4), smax) + _stops(rng, v, v - 1, smax)
        return _text(cfg, rows, _prompts(rng, v, rng.randint(1, 2), 1, 3), rng)

    if fam == "tie":
        # One score for every row, so every order in the contract is decided by its tie-break.
        v = rng.randint(4, 7)
        flat = rng.randint(2, 5)
        rows = [(a, b, flat) for a, b, _s in _edges(rng, v, rng.randint(2, 4), 1)]
        rows += [(a, 0, flat) for a, _b, _s in _stops(rng, v, max(1, v // 2), 1)]
        cfg = (rng.randint(2, 4), 2, 1, rng.randint(0, 2), rng.randint(2, 4), rng.randint(8, 16))
        return _text(cfg, rows, _prompts(rng, v, rng.randint(2, 3), 1, 3), rng)

    if fam == "dry":
        # Thin graphs under a high ceiling, so the search runs out rather than being stopped.
        v = rng.randint(3, 5)
        cfg = (rng.randint(2, 4), 2, 1, rng.randint(0, 1), rng.randint(2, 4), rng.randint(20, 30))
        rows = _edges(rng, v, 1, 5) + _stops(rng, v, max(1, v - 2), 5)
        return _text(cfg, rows, _prompts(rng, v, rng.randint(1, 3), 1, 3), rng)

    if fam == "wide":
        # One long search per request, with a floor that keeps the kept set out of the way for
        # the first two hundred steps, so what the limit measures is the cost of carrying each
        # beam's spans rather than rebuilding them from its tokens.
        v = 26
        cfg = (8, 4, 200, 1, 2, 2800)
        rows = _edges(rng, v, 10, 60) + _stops(rng, v, 2, 60)
        return _text(cfg, rows, _prompts(rng, v, 5, 2, 4), rng)

    if fam == "churn":
        # A kept set that turns over on nearly every step of a long search, so the lent spans
        # have to be combined from records rather than counted out of the members' tokens.
        v = 40
        cfg = (6, 4, 1, 4, 30, 900)
        rows = _edges(rng, v, 9, 9) + _stops(rng, v, 30, 9)
        return _text(cfg, rows, _prompts(rng, v, 5, 2, 4), rng)

    raise ValueError(fam)


def programs(seed, per):
    out = []
    for fam, big in FAMILIES:
        how = BIG if big else per
        for i in range(how):
            rng = random.Random("%s|%s|%d" % (seed, fam, i))
            out.append((fam, "%s-%d" % (fam, i), make(fam, rng)))
    return out
