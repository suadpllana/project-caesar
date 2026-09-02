"""Register generator.

Deterministic for a given seed, and deterministic ACROSS PROCESSES: the runner builds the
graded registers in one process and the grader rebuilds them in another, so every
collection this file turns into a sequence is sorted first. Nothing here iterates a set or
a dict keyed by strings without sorting it.

Shapes are chosen so that the two things a submission has to get right actually occur:
companies carrying more than one hand of the same side, and holding chains that run
backwards through the incorporation order.

Every register it emits is TIE FREE, and that is a correctness requirement rather than a
nicety. A seat taken on a tied average would be settled by whatever name the hands happen
to carry, and the name a submission gives to a hand of several holders is its own
business, so a tied seat would make two correct submissions disagree. `clean` checks every
way the holders of a company could be split into one combined hand and singletons, which
covers every grouping any determination can produce, and the builder perturbs the lot
sizes until nothing ties.
"""

from __future__ import annotations

import random

SEATS = (2, 3, 3, 3, 4, 5, 5, 7)
VPS = (1, 1, 2, 5, 10)
LOTS = (50, 80, 110, 130, 170, 190, 230, 290, 310, 370, 410, 530)
TRIES = 60


def _ids(prefix, n):
    return ["%s%d" % (prefix, i) for i in range(1, n + 1)]


def _replay(lines):
    """Company -> {casting party: votes}, by the same rules the register states."""
    seat, weight, stock, nom, order = {}, {}, {}, {}, []
    for raw in lines:
        b = raw.split()
        if b[0] == "co":
            order.append(b[1])
            seat[b[1]] = int(b[2])
        elif b[0] == "cl":
            weight[(b[1], b[2])] = int(b[3])
        elif b[0] == "is":
            key = (b[1], b[2], b[4])
            stock[key] = stock.get(key, 0) + int(b[3])
        elif b[0] == "mv":
            stock[(b[1], b[2], b[4])] = stock.get((b[1], b[2], b[4]), 0) - int(b[3])
            stock[(b[1], b[2], b[5])] = stock.get((b[1], b[2], b[5]), 0) + int(b[3])
        elif b[0] == "nm":
            nom[b[1]] = b[2]
        elif b[0] == "nx":
            nom.pop(b[1], None)

    def caster(who):
        step, walked = who, [who]
        while step in nom:
            step = nom[step]
            if step in walked:
                return walked[0]
            walked.append(step)
        return step

    out = {c: {} for c in order}
    for (co, kind, who), n in sorted(stock.items()):
        if n <= 0 or who == co:
            continue
        w = weight[(co, kind)] * n
        if w <= 0:
            continue
        v = caster(who)
        if v == co:
            continue
        out[co][v] = out[co].get(v, 0) + w
    return seat, order, out


def _ties(hands, seats):
    got = {k: 0 for k in hands if hands[k] > 0}
    live = sorted(got)
    for _ in range(seats):
        if not live:
            return False
        best = live[0]
        for k in live[1:]:
            if hands[k] * (got[best] + 1) > hands[best] * (got[k] + 1):
                best = k
        for k in live:
            if k != best and hands[k] * (got[best] + 1) == hands[best] * (got[k] + 1):
                return True
        got[best] += 1
    return False


def clean(lines):
    """No seat in any company is ever taken on a tied average, under any grouping."""
    seat, order, votes = _replay(lines)
    for co in order:
        who = sorted(k for k in votes[co] if votes[co][k] > 0)
        if len(who) > 8:
            return False
        for mask in range(1 << len(who)):
            hands = {}
            lump = 0
            for i, k in enumerate(who):
                if mask & (1 << i):
                    lump += votes[co][k]
                else:
                    hands[k] = votes[co][k]
            if lump:
                hands["+"] = lump
            if _ties(hands, seat[co]):
                return False
    return True


def _draft(rng):
    nk = rng.randint(2, 7)
    nh = rng.randint(2, 5)
    nn = rng.randint(0, 3)
    cos = _ids("k", nk)
    folk = _ids("h", nh)
    noms = _ids("n", nn)

    seats = {c: rng.choice(SEATS) for c in cos}
    kinds = {}
    for c in cos:
        ks = ["o", "p"] if rng.random() < 0.35 else ["o"]
        kinds[c] = [(k, rng.choice(VPS)) for k in ks]

    nom = {}
    for i, who in enumerate(noms):
        pool = folk + noms[:i]
        if rng.random() < 0.45:
            pool = pool + cos
        nom[who] = rng.choice(pool)

    named = sorted(rng.sample(folk, rng.randint(1, min(3, nh))))
    holders = sorted(folk + noms)
    plan = []
    for c in cos:
        pool = sorted(holders + [x for x in cos if x != c])
        want = rng.randint(2, 5) if rng.random() < 0.55 else rng.randint(2, 3)
        who = sorted(rng.sample(pool, min(want, len(pool))))
        if len(named) > 1 and rng.random() < 0.6:
            who = sorted(set(who) | set(named))
        # A company's own stock, standing in somebody else's name. The frozen accessor
        # drops the holding recorded against the company itself, so this is the half of
        # the treasury rule a submission has to see for itself.
        mine = sorted(k for k in nom if nom[k] == c)
        if mine and rng.random() < 0.85:
            who = sorted(set(who) | {rng.choice(mine)})
        own = {k for k in nom if nom[k] == c}
        plan.append((c, [(h, rng.choice(kinds[c])[0],
                          rng.choice(LOTS[-5:]) if h in own else rng.choice(LOTS))
                         for h in who]))

    late = []
    for i, (c, who) in enumerate(plan):
        if rng.random() < 0.25 and who:
            j = rng.randrange(len(who))
            late.append((c, who[j][1], 50, who[j][0]))
    drop = rng.choice(sorted(noms)) if (noms and rng.random() < 0.3) else None
    return cos, folk, noms, seats, kinds, nom, named, plan, late, drop


def _lines(seats, kinds, nom, named, plan, late, drop, bump):
    out = ["pg %s" % w for w in named]
    for i, (c, who) in enumerate(plan):
        out.append("co %s %d" % (c, seats[c]))
        for k, w in kinds[c]:
            out.append("cl %s %s %d" % (c, k, w))
        for j, (h, k, lot) in enumerate(who):
            out.append("is %s %s %d %s" % (c, k, lot + bump.get((i, j), 0), h))
    for who in sorted(nom):
        out.append("nm %s %s" % (who, nom[who]))
    for c, k, n, src in late:
        out.append("mv %s %s %d %s %s" % (c, k, n, src, c))
    if drop:
        out.append("nx %s" % drop)
    return out


def build(seed):
    rng = random.Random(seed)
    cos, folk, noms, seats, kinds, nom, named, plan, late, drop = _draft(rng)
    spots = sorted((i, j) for i, (_, who) in enumerate(plan) for j in range(len(who)))
    bump = {}
    for _ in range(TRIES):
        lines = _lines(seats, kinds, nom, named, plan, late, drop, bump)
        if clean(lines):
            return "\n".join(lines) + "\n"
        spot = spots[rng.randrange(len(spots))]
        bump[spot] = bump.get(spot, 0) + rng.choice((1, 3, 7, 13))
    return None


def batch(nonce, count):
    """`count` tie-free registers, named g0000.., derived from a run nonce."""
    out, i, guard = [], 0, 0
    while len(out) < count and guard < count * 40:
        text = build("%s:%d" % (nonce, i))
        i += 1
        guard += 1
        if text is not None:
            out.append(("g%04d" % len(out), text))
    return out
