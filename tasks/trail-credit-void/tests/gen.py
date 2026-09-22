"""The graded population, built from a seed the submission never saw.

Eleven families. Nine of them are small and concentrate one mechanism each, because a trail
generated without a shape in mind exercises none of them: a wrong reading of the re-arm rule
moves under one per cent of unshaped trails and a third of the `rearm` family. The last two are
the scale families the execution limit is measured against - one with fifty thousand records and
sixteen thousand steps, one with a rubric of four thousand six hundred goals over forty-two
thousand steps.

Every maker drives the records towards the predicates its rubric names, so goals are actually
reached; noise is added around that rather than hoped for.
"""
import random

FAMILIES = (
    ("plain", False),
    ("chain", False),
    ("fail", False),
    ("bar", False),
    ("rearm", False),
    ("settle", False),
    ("budget", False),
    ("carry", False),
    ("edge", False),
    ("wide", True),
    ("deep", True),
)

BIG_EACH = 3


def _goal(gid, weight, pre, kind, key, val=None):
    head = "goal %d %d %d" % (gid, weight, len(pre))
    if pre:
        head += " " + " ".join(str(x) for x in pre)
    if kind == "off":
        return "%s off %d" % (head, key)
    return "%s %s %d %d" % (head, kind, key, val)


def _rubric(rnd, out, goals, keys, chainy=0.5, bars=0, kinds=("at", "up", "off")):
    """A rubric over `keys`, returning the goal records so a maker can aim at them."""
    made = []
    for gid in range(goals):
        pre = []
        if gid and rnd.random() < chainy:
            pre = sorted(rnd.sample(range(gid), min(gid, rnd.randrange(1, 3))))
        kind = rnd.choice(kinds)
        key = rnd.choice(keys)
        val = None if kind == "off" else rnd.randrange(2, 9)
        out.append(_goal(gid, rnd.randrange(1, 4), pre, kind, key, val))
        made.append((gid, pre, kind, key, val))
    for bid in range(bars):
        out.append("bar %d %d %s %d" % (bid, rnd.randrange(goals),
                                        rnd.choice(("lost", "gain", "back")),
                                        rnd.choice(keys)))
    return made


def _aim(rnd, made, keys):
    """One action that moves a record towards or away from some goal's predicate."""
    gid, _pre, kind, key, val = made[rnd.randrange(len(made))]
    roll = rnd.random()
    if kind == "off":
        return "cut %d" % key if roll < 0.6 else "put %d %d" % (key, rnd.randrange(1, 9))
    if roll < 0.55:
        return "put %d %d" % (key, val)
    if roll < 0.75:
        return "put %d %d" % (key, max(0, val - rnd.randrange(1, 3)))
    if roll < 0.9:
        return "put %d %d" % (key, val + rnd.randrange(1, 3))
    return "cut %d" % key


def _steps(rnd, made, keys, count, fail_rate=0.0, per=(1, 3)):
    out = []
    for _ in range(count):
        out.append("step")
        for _ in range(rnd.randrange(per[0], per[1] + 1)):
            out.append(_aim(rnd, made, keys))
        out.append("err" if rnd.random() < fail_rate else "ok")
    return out


def _head(budget, seeds):
    out = ["cfg %d" % budget]
    for key, value in seeds:
        out.append("rec %d %d" % (key, value))
    return out


def plain(rnd):
    """Ordinary runs: room in the budget, no violation, credit earned in order."""
    keys = list(range(rnd.randrange(4, 8)))
    seeds = [(key, rnd.randrange(1, 9)) for key in keys if rnd.random() < 0.7]
    out = _head(4000, seeds)
    for ep in range(rnd.randrange(1, 3)):
        out.append("ep p%d" % ep)
        made = _rubric(rnd, out, rnd.randrange(3, 7), keys, chainy=0.5)
        out.extend(_steps(rnd, made, keys, rnd.randrange(6, 18)))
    return out


def chain(rnd):
    """Long prerequisite runs, several links satisfied inside one step."""
    keys = list(range(rnd.randrange(3, 6)))
    out = _head(4000, [(key, 1) for key in keys])
    out.append("ep c0")
    goals = rnd.randrange(4, 8)
    made = []
    for gid in range(goals):
        pre = [gid - 1] if gid else []
        key = keys[gid % len(keys)]
        val = 2 + gid
        out.append(_goal(gid, rnd.randrange(1, 4), pre, "up", key, val))
        made.append((gid, pre, "up", key, val))
    steps = []
    for turn in range(rnd.randrange(4, 10)):
        steps.append("step")
        for gid, _pre, _kind, key, val in made:
            if rnd.random() < 0.55:
                steps.append("put %d %d" % (key, val + rnd.randrange(0, 2)))
        if steps[-1] == "step":
            steps.append(_aim(rnd, made, keys))
        steps.append("ok" if rnd.random() < 0.85 else "err")
    out.extend(steps)
    return out


def fail(rnd):
    """Steps that end err: rolled back, and no observation from them."""
    keys = list(range(rnd.randrange(3, 7)))
    out = _head(4000, [(key, rnd.randrange(1, 6)) for key in keys])
    out.append("ep f0")
    made = _rubric(rnd, out, rnd.randrange(3, 7), keys, chainy=0.6,
                   bars=rnd.randrange(1, 4))
    out.extend(_steps(rnd, made, keys, rnd.randrange(8, 20), fail_rate=0.45))
    return out


def bar(rnd):
    """Violations that fire on goals other goals stand on."""
    keys = list(range(rnd.randrange(3, 6)))
    out = _head(4000, [(key, rnd.randrange(2, 7)) for key in keys])
    out.append("ep b0")
    goals = rnd.randrange(4, 8)
    made = []
    for gid in range(goals):
        pre = sorted(rnd.sample(range(gid), min(gid, rnd.randrange(1, 3)))) if gid else []
        kind = rnd.choice(("at", "up", "up"))
        key = rnd.choice(keys)
        val = rnd.randrange(2, 7)
        out.append(_goal(gid, rnd.randrange(1, 4), pre, kind, key, val))
        made.append((gid, pre, kind, key, val))
    for bid in range(rnd.randrange(1, 4)):
        out.append("bar %d %d %s %d" % (bid, rnd.randrange(max(1, goals - 2)),
                                        rnd.choice(("lost", "back", "back")),
                                        rnd.choice(keys)))
    steps = []
    for turn in range(rnd.randrange(8, 18)):
        steps.append("step")
        if rnd.random() < 0.35:
            key = rnd.choice(keys)
            steps.append("cut %d" % key if rnd.random() < 0.5
                         else "put %d %d" % (key, 1))
        else:
            for _ in range(rnd.randrange(1, 3)):
                steps.append(_aim(rnd, made, keys))
        steps.append("ok" if rnd.random() < 0.9 else "err")
    out.extend(steps)
    return out


def rearm(rnd):
    """Goals shut while their predicate already fails, and while it still holds."""
    keys = list(range(3))
    out = _head(4000, [(0, 5), (1, 5), (2, 5)])
    out.append("ep r0")
    made = []
    made.append((0, [], "up", 0, 3))
    out.append(_goal(0, 2, [], "up", 0, 3))
    made.append((1, [0], "up", 1, 3))
    out.append(_goal(1, 3, [0], "up", 1, 3))
    made.append((2, [], "off", 2, None))
    out.append(_goal(2, 1, [], "off", 2))
    out.append("bar 0 0 back 0")
    out.append("bar 1 2 gain 2")
    steps = []
    for turn in range(rnd.randrange(10, 22)):
        steps.append("step")
        roll = rnd.random()
        if roll < 0.3:
            steps.append("put 0 %d" % rnd.randrange(1, 3))
        elif roll < 0.55:
            steps.append("put 0 %d" % rnd.randrange(3, 8))
        elif roll < 0.7:
            steps.append("cut 2")
        elif roll < 0.85:
            steps.append("put 2 %d" % rnd.randrange(1, 5))
        else:
            steps.append("put 1 %d" % rnd.randrange(1, 8))
        if rnd.random() < 0.4:
            steps.append("put %d %d" % (rnd.choice(keys), rnd.randrange(1, 8)))
        steps.append("ok" if rnd.random() < 0.88 else "err")
    out.extend(steps)
    return out


def settle(rnd):
    """Predicates that stop holding with no violation anywhere."""
    keys = list(range(rnd.randrange(3, 6)))
    out = _head(4000, [(key, 6) for key in keys])
    out.append("ep s0")
    made = _rubric(rnd, out, rnd.randrange(3, 6), keys, chainy=0.4, kinds=("at", "up"))
    steps = []
    for turn in range(rnd.randrange(8, 16)):
        steps.append("step")
        if turn % 2:
            key = rnd.choice(keys)
            steps.append("cut %d" % key if rnd.random() < 0.5 else "put %d 0" % key)
        else:
            steps.append(_aim(rnd, made, keys))
        steps.append("ok")
    out.extend(steps)
    return out


def budget(rnd):
    """Budgets that run out inside a step, and episodes closed short."""
    keys = list(range(rnd.randrange(3, 6)))
    spend = rnd.randrange(3, 14)
    out = _head(spend, [(key, rnd.randrange(1, 7)) for key in keys])
    for ep in range(rnd.randrange(1, 4)):
        out.append("ep g%d" % ep)
        made = _rubric(rnd, out, rnd.randrange(2, 5), keys, chainy=0.4,
                       bars=rnd.randrange(0, 3))
        out.extend(_steps(rnd, made, keys, rnd.randrange(4, 12),
                          fail_rate=0.3, per=(1, 4)))
    return out


def carry(rnd):
    """Several episodes over one set of records, some closed short."""
    keys = list(range(rnd.randrange(3, 6)))
    out = _head(rnd.randrange(6, 20), [(key, rnd.randrange(2, 7)) for key in keys])
    for ep in range(rnd.randrange(2, 5)):
        out.append("ep k%d" % ep)
        made = _rubric(rnd, out, rnd.randrange(2, 5), keys, chainy=0.5,
                       bars=rnd.randrange(1, 3))
        out.extend(_steps(rnd, made, keys, rnd.randrange(3, 9), fail_rate=0.2))
    return out


def edge(rnd):
    """Values sitting exactly on a threshold, zeroes, and keys never seeded."""
    keys = list(range(5))
    seeds = [(0, 0), (1, 4)]
    if rnd.random() < 0.5:
        seeds.append((2, 0))
    out = _head(4000, seeds)
    out.append("ep e0")
    made = []
    out.append(_goal(0, 2, [], "up", 1, 4))
    made.append((0, [], "up", 1, 4))
    out.append(_goal(1, 1, [], "off", 0))
    made.append((1, [], "off", 0, None))
    out.append(_goal(2, 3, [0], "at", 3, 0))
    made.append((2, [0], "at", 3, 0))
    out.append(_goal(3, 1, [], "off", 4))
    made.append((3, [], "off", 4, None))
    out.append("bar 0 0 gain 3")
    steps = []
    for turn in range(rnd.randrange(6, 14)):
        steps.append("step")
        roll = rnd.random()
        if roll < 0.25:
            steps.append("put 1 %d" % rnd.choice((3, 4, 5)))
        elif roll < 0.45:
            steps.append("put 3 0")
        elif roll < 0.6:
            steps.append("cut 3")
        elif roll < 0.75:
            steps.append("put 0 0")
        elif roll < 0.9:
            steps.append("cut 0")
        else:
            steps.append("put 4 %d" % rnd.randrange(0, 3))
        steps.append("ok" if rnd.random() < 0.9 else "err")
    out.extend(steps)
    return out


def wide(rnd, recs=50000, steps=16000, goals=30, bars=8):
    """Fifty thousand records: a copy of them per step or per observation cannot finish."""
    out = ["cfg %d" % (steps * 3 + 16)]
    for key in range(recs):
        out.append("rec %d %d" % (key, rnd.randrange(4, 60)))
    out.append("ep wide")
    hot = sorted(rnd.sample(range(recs), goals))
    for gid in range(goals):
        pre = [] if gid == 0 or rnd.random() < 0.3 else [rnd.randrange(gid)]
        kind = rnd.choice(("at", "up", "up"))
        out.append(_goal(gid, rnd.randrange(1, 4), pre, kind, hot[gid],
                         rnd.randrange(4, 60)))
    for bid in range(bars):
        out.append("bar %d %d %s %d" % (bid, rnd.randrange(goals),
                                        rnd.choice(("lost", "back", "gain")),
                                        hot[rnd.randrange(goals)]))
    for _turn in range(steps):
        out.append("step")
        for _ in range(rnd.randrange(1, 4)):
            key = hot[rnd.randrange(goals)] if rnd.random() < 0.12 \
                else rnd.randrange(recs)
            out.append("cut %d" % key if rnd.random() < 0.15
                       else "put %d %d" % (key, rnd.randrange(1, 70)))
        out.append("ok" if rnd.random() < 0.85 else "err")
    return out


def deep(rnd, recs=400, steps=42000, goals=4600, bars=240):
    """A rubric of four thousand six hundred goals: sweeping it per observation cannot finish."""
    out = ["cfg %d" % (steps * 3 + 16)]
    for key in range(recs):
        out.append("rec %d %d" % (key, rnd.randrange(4, 40)))
    out.append("ep deep")
    for gid in range(goals):
        room = min(gid, 6)
        pre = sorted(rnd.sample(range(gid - room, gid),
                                min(room, rnd.randrange(0, 4)))) if room else []
        kind = rnd.choice(("at", "up", "up", "off"))
        key = rnd.randrange(recs)
        val = None if kind == "off" else rnd.randrange(4, 40)
        out.append(_goal(gid, rnd.randrange(1, 4), pre, kind, key, val))
    for bid in range(bars):
        out.append("bar %d %d %s %d" % (bid, rnd.randrange(goals),
                                        rnd.choice(("lost", "back", "gain")),
                                        rnd.randrange(recs)))
    for _turn in range(steps):
        out.append("step")
        for _ in range(rnd.randrange(1, 4)):
            key = rnd.randrange(recs)
            out.append("cut %d" % key if rnd.random() < 0.18
                       else "put %d %d" % (key, rnd.randrange(1, 44)))
        out.append("ok" if rnd.random() < 0.85 else "err")
    return out


MAKERS = {
    "plain": plain,
    "chain": chain,
    "fail": fail,
    "bar": bar,
    "rearm": rearm,
    "settle": settle,
    "budget": budget,
    "carry": carry,
    "edge": edge,
    "wide": wide,
    "deep": deep,
}


def programs(seed, per):
    """Every graded trail that was not written by hand, in a fixed order."""
    out = []
    for fam, big in FAMILIES:
        count = BIG_EACH if big else per
        for turn in range(count):
            rnd = random.Random("%s|%s|%d" % (seed, fam, turn))
            out.append((fam, "%s-%d" % (fam, turn), MAKERS[fam](rnd)))
    return out
