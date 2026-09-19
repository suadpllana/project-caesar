"""Programs generated from a seed drawn after the agent's container is gone.

The families are shaped around the decisions rather than sampled from the input space. An
unshaped population is almost all trees: every row is reached once, by one link, at one depth,
so the group rule, the merge rule and the restrict timing never separate from their wrong
readings and a broken service scores the same as a right one. Each family below concentrates
one mechanism by making the shape that exercises it common instead of rare, and the two scale
families exist for the execution limit rather than for a rule.

  chain    long runs of removing links, so groups go several deep
  fork     every table pair linked, so rows are reached by a short route and a longer one
  share    one pointer column per table with many links onto it, from several parents
  keymove  re-keys, with links onto key columns so a follow carries on from the row it lands on
  barwait  restrict and deferred links mixed in, over rows the change would itself remove
  undoing  deferred links that stop changes, with later changes over the same rows
  clashing re-keys into a key space small enough that the new key is usually held
  mixed    all of it at once, nothing concentrated
  wideout  one large store under many removals, for the execution limit
  widemov  one large store under many re-keys, for the execution limit
"""
import random

FAMILIES = (
    ("chain", False),
    ("fork", False),
    ("share", False),
    ("keymove", False),
    ("barwait", False),
    ("undoing", False),
    ("clashing", False),
    ("mixed", False),
    ("wideout", True),
    ("widemov", True),
)

BIG = 2

TABS = ("a", "b", "c", "d", "e")
COLS = ("p", "q", "r")

# (goes, moves) pairs, drawn per link. A key column takes only the pairs without a clear.
FULL = (("drop", "follow"), ("drop", "follow"), ("drop", "clear"), ("clear", "follow"),
        ("clear", "clear"), ("drop", "wait"), ("wait", "follow"), ("bar", "follow"),
        ("drop", "bar"))
CUTS = (("drop", "follow"), ("drop", "follow"), ("drop", "bar"), ("drop", "wait"),
        ("wait", "follow"), ("bar", "follow"))
STOPS = (("bar", "bar"), ("wait", "wait"), ("bar", "wait"), ("wait", "bar"),
         ("drop", "follow"), ("clear", "clear"), ("wait", "follow"), ("drop", "wait"))
HOLDS = (("wait", "wait"), ("wait", "follow"), ("drop", "wait"), ("drop", "follow"),
         ("wait", "bar"))


def _keyok(pair):
    return pair[0] != "clear" and pair[1] != "clear"


def _head(rng, ntab, colmax, pairp, pool, keyp):
    """Tables in declaration order; links only ever from an earlier table to a later one."""
    lines, tabs, links = [], [], []
    for i in range(ntab):
        cols = ["k"] + sorted(rng.sample(COLS, rng.randint(1, colmax)))
        tabs.append((TABS[i], cols))
        lines.append("tab %s %s" % (TABS[i], " ".join(cols)))
    for j in range(ntab):
        for i in range(j):
            if rng.random() >= pairp:
                continue
            kid, kcols = tabs[j]
            par = tabs[i][0]
            if rng.random() < keyp:
                col = "k"
                goes, moves = rng.choice([p for p in pool if _keyok(p)])
            else:
                col = rng.choice(kcols[1:])
                goes, moves = rng.choice(pool)
            name = "l%d" % len(links)
            links.append(name)
            lines.append("link %s %s %s %s %s %s" % (name, kid, col, par, goes, moves))
    return lines, tabs


def _rows(rng, tabs, span, rows, emptyp, wildp):
    """Keys are drawn from one small span across every table, so a pointer often names a
    row in more than one parent - which is what puts two links on one column."""
    lines, held = [], {}
    for name, cols in tabs:
        keys = sorted(rng.sample(range(1, span + 1), min(rows, span)))
        held[name] = keys
        for key in keys:
            vals = [str(key)]
            for _col in cols[1:]:
                pick = rng.random()
                if pick < emptyp:
                    vals.append("-")
                elif pick < emptyp + wildp:
                    vals.append(str(rng.randint(span + 1, span + 5)))
                else:
                    vals.append(str(rng.randint(1, span)))
            lines.append("put %s %s" % (name, " ".join(vals)))
    return lines, held


def _acts(rng, tabs, held, count, kinds, span, movspan):
    lines = []
    for _ in range(count):
        name = rng.choice([t[0] for t in tabs])
        kind = rng.choice(kinds)
        if rng.random() < 0.88 and held[name]:
            key = rng.choice(held[name])
        else:
            key = rng.randint(1, span + 4)
        if kind == "out":
            lines.append("out %s %d" % (name, key))
        else:
            lines.append("mov %s %d %d" % (name, key, rng.randint(1, movspan)))
    return lines


def _big(rng, kind):
    """One store large enough that finding a link's rows by walking them does not finish.

    Every change names a key of its own, so the cost is paid once per change rather than
    saved by a repeat that finds nothing there.
    """
    tops, mids, lows, hits = 9000, 63000, 30000, 9000
    lines = ["tab a k", "tab b k p", "tab c k p q"]
    lines.append("link l0 b p a drop follow")
    lines.append("link l1 c p b drop follow")
    lines.append("link l2 c q a wait wait")
    lines.append("link l3 b p a wait wait")
    for key in range(1, tops + 1):
        lines.append("put a %d" % key)
    for key in range(1, mids + 1):
        lines.append("put b %d %d" % (key, rng.randint(1, tops)))
    for key in range(1, lows + 1):
        lines.append("put c %d %d %d" % (key, rng.randint(1, mids),
                                         rng.randint(tops + 1, tops + 60)))
    picks = list(range(1, tops + 1))
    rng.shuffle(picks)
    for i in range(hits):
        key = picks[i]
        if kind == "out":
            lines.append("out a %d" % key)
        else:
            lines.append("mov a %d %d" % (key, tops + 61 + i))
    return lines


def build(fam, rng):
    if fam == "chain":
        lines, tabs = _head(rng, rng.randint(4, 5), 2, 0.45, CUTS, 0.25)
        put, held = _rows(rng, tabs, 11, 8, 0.12, 0.1)
        return lines + put + _acts(rng, tabs, held, rng.randint(5, 9), ("out",), 11, 20)

    if fam == "fork":
        lines, tabs = _head(rng, rng.randint(3, 4), 2, 1.0, CUTS, 0.15)
        put, held = _rows(rng, tabs, 9, 7, 0.1, 0.08)
        return lines + put + _acts(rng, tabs, held, rng.randint(5, 9), ("out", "out", "mov"),
                                   9, 20)

    if fam == "share":
        lines, tabs = _head(rng, rng.randint(3, 5), 1, 1.0, FULL, 0.1)
        put, held = _rows(rng, tabs, 7, 7, 0.06, 0.06)
        return lines + put + _acts(rng, tabs, held, rng.randint(5, 9), ("out", "out", "mov"),
                                   7, 16)

    if fam == "keymove":
        lines, tabs = _head(rng, rng.randint(3, 5), 2, 0.7, CUTS, 0.75)
        put, held = _rows(rng, tabs, 10, 9, 0.08, 0.06)
        return lines + put + _acts(rng, tabs, held, rng.randint(5, 9), ("mov", "mov", "out"),
                                   10, 26)

    if fam == "barwait":
        lines, tabs = _head(rng, rng.randint(3, 5), 2, 0.8, STOPS, 0.2)
        put, held = _rows(rng, tabs, 9, 8, 0.1, 0.12)
        return lines + put + _acts(rng, tabs, held, rng.randint(6, 10), ("out", "out", "mov"),
                                   9, 20)

    if fam == "undoing":
        lines, tabs = _head(rng, rng.randint(3, 4), 2, 0.9, HOLDS, 0.2)
        put, held = _rows(rng, tabs, 8, 8, 0.05, 0.05)
        return lines + put + _acts(rng, tabs, held, rng.randint(8, 12), ("out", "out", "mov"),
                                   8, 14)

    if fam == "clashing":
        lines, tabs = _head(rng, rng.randint(3, 4), 2, 0.8, CUTS, 0.55)
        put, held = _rows(rng, tabs, 6, 6, 0.05, 0.05)
        return lines + put + _acts(rng, tabs, held, rng.randint(6, 10), ("mov",), 6, 8)

    if fam == "mixed":
        lines, tabs = _head(rng, rng.randint(3, 5), 3, 0.6, FULL, 0.3)
        put, held = _rows(rng, tabs, 12, 9, 0.12, 0.12)
        return lines + put + _acts(rng, tabs, held, rng.randint(6, 11), ("out", "mov"), 12, 30)

    if fam == "wideout":
        return _big(rng, "out")

    if fam == "widemov":
        return _big(rng, "mov")

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
