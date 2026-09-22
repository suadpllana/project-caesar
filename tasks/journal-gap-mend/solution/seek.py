# Reference settle of the whole journal: forward over every line, backward from the final
# audit, then one walk per lost span.
from jl import fp, say, span, table, tally, walk
from jl.read import Dig, Entry, Gap


def _step(node, rec, journal):
    """A surviving line. A node carries the digest its last entry obliges the next line to be."""
    t, s, due = node
    if isinstance(rec, Entry):
        if due is not None:
            return None
        got = table.offer(t, rec.kind, rec.lock, rec.sess)
        if got is None or got[0] != rec.out:
            return None
        t2 = got[1]
        s2 = tally.add(s, rec.kind, rec.out)
        return t2, s2, ((s2.grants, fp.holders(t2)) if tally.due(s, s2, journal.period) else None)
    if isinstance(rec, Dig):
        return (t, s, None) if due == (rec.grants, rec.mark) else None
    if due is None and s == tally.seen(rec) and fp.whole(t) == rec.mark:
        return node
    return None


def _rank(node):
    s, j = node[1], node[2]
    return s.asks + s.rels + s.beats, j


def mend(journal):
    items = journal.items
    layer = {(table.start(journal.locks), tally.ZERO, None)}
    steps = []
    for at, rec in enumerate(items):
        if isinstance(rec, Gap):
            starts = {(t, s) for t, s, due in layer if due is None}
            edges, exits = span.expand(starts, rec, journal, tally.room(items, at))
            steps.append((starts, edges, exits))
            layer = {(t, s, None) for t, s, _j in exits}
        else:
            moves = {}
            for node in layer:
                nxt = _step(node, rec, journal)
                if nxt is not None:
                    moves[node] = nxt
            steps.append(moves)
            layer = set(moves.values())

    live = layer
    lives = {}
    for at in range(len(items) - 1, -1, -1):
        step = steps[at]
        if isinstance(step, dict):
            live = {a for a, b in step.items() if b in live}
            continue
        starts, edges, exits = step
        after = {(t, s) for t, s, _due in live}
        ok = set()
        for node in sorted(edges, key=_rank, reverse=True):
            if (node in exits and node[:2] in after) or any(v in ok for _e, v in edges[node]):
                ok.add(node)
        lives[at] = (ok, after)
        live = {(t, s, None) for t, s in starts if (t, s, 0) in ok}

    lines = []
    n = 0
    for at, rec in enumerate(items):
        if isinstance(rec, Gap):
            n += 1
            starts, edges, exits = steps[at]
            ok, after = lives[at]
            restored, cands = walk.agree(starts, edges, exits, ok, after)
            lines.extend(say.span(n, restored, cands))
    return lines
