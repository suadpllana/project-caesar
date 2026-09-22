# Reference expansion of one lost span into a graph of inner nodes.
from jl import fp, table, tally
from jl.read import Aud, Entry


def expand(starts, gap, journal, cap):
    """Every way to fill the span from every start node.

    An inner node is (table, totals, j): j markers of the span consumed so far, in order. A
    digest is consumed exactly when the entry that triggers it is taken; an audit may be
    consumed at any inner node whose totals and whole table match it, by an edge whose entry
    is None. Returns (edges, exits): edges maps an inner node to [(entry, inner node)], exits
    are the inner nodes that have consumed every marker and may leave the span."""
    marks = gap.marks
    last = len(marks)
    edges = {}
    exits = set()
    todo = [(t, s, 0) for t, s in starts]
    seen = set(todo)
    while todo:
        node = todo.pop()
        t, s, j = node
        out = []
        mark = marks[j] if j < last else None
        if isinstance(mark, Aud) and s == tally.seen(mark) and fp.whole(t) == mark.mark:
            out.append((None, (t, s, j + 1)))
        if j == last:
            exits.add(node)
        for kind, lock, sess, res, t2 in table.moves(t, journal.locks, journal.sessions):
            s2 = tally.add(s, kind, res)
            if (s2.grants > cap.grants or s2.asks > cap.asks or s2.rels > cap.rels
                    or s2.beats > cap.beats):
                continue
            j2 = j
            if tally.due(s, s2, journal.period):
                if mark is None or isinstance(mark, Aud) or mark != (s2.grants, fp.holders(t2)):
                    continue                        # no digest here for it to write
                j2 = j + 1
            out.append((Entry(kind, lock, sess, res), (t2, s2, j2)))
        edges[node] = out
        for _e, nxt in out:
            if nxt not in seen:
                seen.add(nxt)
                todo.append(nxt)
    return edges, exits
