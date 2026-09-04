"""The definitional model, written a second time and a different way.

The engine in the environment fills a table backwards from the end. This one
walks forwards: it settles, for every position and every number of kept lines
since the last move, the cheapest (moves, changes) pair that reaches it, and
only then reads the script off by preferring a drop, then an add, then a keep
among the steps that stay on an optimal route. The two share no code, so a
misreading of the rule has to be made twice in two different shapes to pass
unnoticed.

The board is settled a second way too. The reference carries the whole live
set through one revision at a time; here each note is followed on its own from
the revision it was opened at to the head, and the events are collected per
revision afterwards and ordered at the end. Same rule, opposite arrangement.

Lives in /tests, which the account that runs submitted code cannot read.
"""

CONTEXT = 3
_BIG = (1 << 30, 1 << 30)


def _plus(pair, moves, charge):
    return (pair[0] + moves, pair[1] + charge)


def _togo(before, after):
    """The cheapest (moves, changes) still to be paid from every position and
    every number of kept lines since the last move. Relaxed one position at a
    time from the far end, which is the opposite arrangement to the table the
    environment fills, and reached from the rule rather than from it."""
    n, m = len(before), len(after)
    rest = {}
    for s in range(CONTEXT + 1):
        rest[(n, m, s)] = (0, 0)
    for i in range(n, -1, -1):
        for j in range(m, -1, -1):
            if i == n and j == m:
                continue
            for s in range(CONTEXT + 1):
                charge = 1 if s == CONTEXT else 0
                got = _BIG
                if i < n:
                    nxt = rest[(i + 1, j, 0)]
                    if nxt < _BIG:
                        cand = _plus(nxt, 1, charge)
                        if cand < got:
                            got = cand
                if j < m:
                    nxt = rest[(i, j + 1, 0)]
                    if nxt < _BIG:
                        cand = _plus(nxt, 1, charge)
                        if cand < got:
                            got = cand
                if i < n and j < m and before[i] == after[j]:
                    nxt = rest[(i + 1, j + 1, s + 1 if s < CONTEXT else CONTEXT)]
                    if nxt < got:
                        got = nxt
                rest[(i, j, s)] = got
    return rest


def script(before, after):
    """The reading that comes first under drop < add < keep, taken one symbol
    at a time: the smallest symbol whose remaining cost still adds up to the
    cheapest total for the pair."""
    n, m = len(before), len(after)
    rest = _togo(before, after)
    ops = []
    i = j = 0
    s = CONTEXT
    while i < n or j < m:
        want = rest[(i, j, s)]
        charge = 1 if s == CONTEXT else 0
        if i < n and _plus(rest[(i + 1, j, 0)], 1, charge) == want:
            ops.append(("-", i))
            i += 1
            s = 0
        elif j < m and _plus(rest[(i, j + 1, 0)], 1, charge) == want:
            ops.append(("+", j))
            j += 1
            s = 0
        else:
            i += 1
            j += 1
            s = s + 1 if s < CONTEXT else CONTEXT
    return ops


def _walk(before, after):
    ops = script(before, after)
    n, m = len(before), len(after)
    i = j = pos = 0
    out = []
    while i < n or j < m:
        if pos < len(ops) and ops[pos] == ("-", i):
            out.append(("D", i, None))
            i += 1
            pos += 1
        elif pos < len(ops) and ops[pos] == ("+", j):
            out.append(("A", None, j))
            j += 1
            pos += 1
        else:
            out.append(("K", i, j))
            i += 1
            j += 1
    return out


def keeps(before, after):
    return dict((i, j) for kind, i, j in _walk(before, after) if kind == "K")


def changes(before, after):
    out = []
    cur = None
    pend = []
    since = CONTEXT
    for kind, i, j in _walk(before, after):
        if kind == "K":
            since += 1
            if cur is not None:
                if since >= CONTEXT:
                    out.append(cur)
                    cur = None
                    pend = []
                else:
                    pend.append(j)
            continue
        if cur is None:
            cur = set()
        else:
            cur.update(pend)
        pend = []
        since = 0
        if kind == "A":
            cur.add(j)
    if cur is not None:
        out.append(cur)
    return [c for c in out if c]


def board(revs, opens):
    steps = len(revs)
    maps = []
    spans = []
    for t in range(1, steps):
        maps.append(keeps(revs[t - 1], revs[t]))
        spans.append(changes(revs[t - 1], revs[t]))

    born = {}
    for at, nid, line in opens:
        born.setdefault(at, []).append((nid, line))

    where = {}
    events = dict((t, {"retire": [], "raise": [], "absorb": []}) for t in range(steps))
    for nid, line in sorted(born.get(0, [])):
        where[nid] = [0, line]
    _collide(where, 0, events)
    for t in range(1, steps):
        table = maps[t - 1]
        for nid in sorted(where):
            spot = where[nid]
            if spot[1] in table:
                spot[1] = table[spot[1]]
            else:
                events[t]["retire"].append(nid)
        for nid in events[t]["retire"]:
            del where[nid]
        for nid in sorted(where):
            for chunk in spans[t - 1]:
                if where[nid][1] in chunk:
                    events[t]["raise"].append(nid)
                    break
        for nid, line in sorted(born.get(t, [])):
            where[nid] = [t, line]
        _collide(where, t, events)

    log = []
    for t in range(steps):
        for nid in sorted(events[t]["retire"]):
            log.append(["retire", nid])
        for nid in events[t]["raise"]:
            log.append(["raise", nid])
        for nid, owner in sorted(events[t]["absorb"]):
            log.append(["absorb", owner, nid])
    notes = sorted([nid, where[nid][1]] for nid in where)
    return notes, log


def _collide(where, t, events):
    seen = {}
    for nid in sorted(where):
        line = where[nid][1]
        owner = seen.get(line)
        if owner is None:
            seen[line] = nid
        else:
            events[t]["absorb"].append((nid, owner))
    for nid, _owner in events[t]["absorb"]:
        if nid in where:
            del where[nid]
