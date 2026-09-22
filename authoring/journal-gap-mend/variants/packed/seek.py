# Correct variant "packed": layered forward pass, liveness by breadth-first search over
# reverse edges from the ids that complete the journal.
from collections import deque

from jl import fp, say, span, table, tally, walk
from jl.read import Aud, Dig, Entry, Gap


def _line(node, rec, journal):
    t, s, due = node
    if isinstance(rec, Entry):
        if due:
            return None
        got = table.offer(t, rec.kind, rec.lock, rec.sess)
        if not got or got[0] != rec.out:
            return None
        s2 = tally.add(s, rec.kind, rec.out)
        return got[1], s2, ((s2[0], fp.holders(got[1])) if tally.due(s, s2, journal.period) else None)
    if isinstance(rec, Dig):
        return (t, s, None) if due == (rec.grants, rec.mark) else None
    if isinstance(rec, Aud) and not due and s == tally.seen(rec) and fp.whole(t) == rec.mark:
        return node
    return None


def mend(journal):
    items = journal.items
    layers = [{(table.start(journal.locks), tally.ZERO, None)}]
    spans = {}
    maps = {}
    for at, rec in enumerate(items):
        cur = layers[-1]
        if isinstance(rec, Gap):
            starts = [(t, s) for t, s, due in cur if due is None]
            built = span.build(starts, rec, journal, tally.room(items, at))
            spans[at] = built
            _first, nodes, _out, _audit, leave = built
            layers.append({(nodes[k][0], nodes[k][1], None) for k in leave})
        else:
            m = {}
            for x in cur:
                y = _line(x, rec, journal)
                if y is not None:
                    m[x] = y
            maps[at] = m
            layers.append(set(m.values()))

    alive = layers[-1]
    marks = {}
    for at in range(len(items) - 1, -1, -1):
        if at in maps:
            alive = {x for x, y in maps[at].items() if y in alive}
            continue
        first, nodes, out, audit, leave = spans[at]
        ends = {k for k in leave if (nodes[k][0], nodes[k][1], None) in alive}
        back = [[] for _ in nodes]
        for k in range(len(nodes)):
            for _label, _e, m in out[k]:
                back[m].append(k)
            for m in audit[k]:
                back[m].append(k)
        good = set(ends)
        queue = deque(ends)
        while queue:
            m = queue.popleft()
            for k in back[m]:
                if k not in good:
                    good.add(k)
                    queue.append(k)
        marks[at] = (good, ends)
        alive = {(nodes[k][0], nodes[k][1], None) for k in first if k in good}

    lines = []
    count = 0
    for at, rec in enumerate(items):
        if isinstance(rec, Gap):
            count += 1
            first, nodes, out, audit, leave = spans[at]
            good, ends = marks[at]
            restored, cands = walk.agree(first, out, audit, good, ends)
            lines.extend(say.span(count, restored, cands))
    return lines
