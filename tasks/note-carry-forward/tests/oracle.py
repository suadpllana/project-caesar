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


def board(revs, events):
    """Settled the other way round to the reference: threads are held in a
    dictionary keyed by id rather than a list, the events of a revision are
    collected into buckets and ordered at the end, and the merging is driven
    by repeatedly hunting the smallest overlapping pair rather than by walking
    a sorted list. Same rule, opposite arrangement."""
    steps = len(revs)
    opened = {}
    said = {}
    for step, kind, payload in events:
        if kind == "open":
            opened.setdefault(step, []).append(payload)
        else:
            said.setdefault(step, []).append((kind, payload))

    span = {}
    state = {}
    caught = {}
    bucket = dict((t, {"outdated": [], "raise": [], "absorb": []}) for t in range(steps))

    def join(t):
        for nid, lines in opened.get(t, []):
            span[nid] = set(lines)
            state[nid] = "open"
            caught[nid] = False

    def talk(t):
        for kind, nid in said.get(t, []):
            if nid not in state:
                continue
            if kind == "reply" and state[nid] == "open":
                state[nid] = "answered"
            elif kind == "resolve" and state[nid] in ("open", "answered"):
                state[nid] = "resolved"

    def merge(t):
        while True:
            live = sorted(n for n in span if state[n] != "outdated")
            pair = None
            for x in range(len(live)):
                for y in range(x + 1, len(live)):
                    if span[live[x]] & span[live[y]]:
                        pair = (live[x], live[y])
                        break
                if pair:
                    break
            if pair is None:
                return
            owner, taken = pair
            span[owner] |= span[taken]
            if state[taken] == "open":
                state[owner] = "open"
            bucket[t]["absorb"].append((taken, owner))
            del span[taken]
            del state[taken]
            if caught.pop(taken, False):
                caught[owner] = True

    join(0)
    talk(0)
    merge(0)
    for t in range(1, steps):
        table = keeps(revs[t - 1], revs[t])
        hunks = changes(revs[t - 1], revs[t])
        for nid in sorted(span):
            if state[nid] == "outdated":
                continue
            span[nid] = set(table[x] for x in span[nid] if x in table)
            if not span[nid]:
                bucket[t]["outdated"].append(nid)
        for nid in bucket[t]["outdated"]:
            state[nid] = "outdated"
            caught.pop(nid, None)
        for nid in sorted(span):
            if state[nid] == "outdated":
                continue
            now = False
            for chunk in hunks:
                if span[nid] & chunk:
                    now = True
                    break
            if state[nid] != "resolved" and now and not caught.get(nid, False):
                bucket[t]["raise"].append((nid, state[nid] == "answered"))
                if state[nid] == "answered":
                    state[nid] = "open"
            caught[nid] = now
        join(t)
        talk(t)
        merge(t)

    log = []
    for t in range(steps):
        for nid in sorted(bucket[t]["outdated"]):
            log.append(["outdated", nid])
        for nid, was_answered in bucket[t]["raise"]:
            log.append(["raise", nid])
            if was_answered:
                log.append(["reopen", nid])
        held = dict(bucket[t]["absorb"])
        for taken in sorted(held):
            owner = held[taken]
            while owner in held:
                owner = held[owner]
            log.append(["absorb", owner, taken])
    threads = []
    for nid in sorted(span):
        threads.append([nid, state[nid], sorted(span[nid])])
    return threads, log


