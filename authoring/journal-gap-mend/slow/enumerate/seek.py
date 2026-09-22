# Slow correct solver "enumerate": every complete account of the journal, found by depth-first
# search, then each span read off the list of fillings. Exact, and exponential in the number
# of orders the evidence leaves open.
import sys

from jl import fp, say, span, table, tally
from jl.read import Dig, Entry, Gap

sys.setrecursionlimit(20000)


def mend(journal):
    items = journal.items
    n = len(items)
    caps = {i: tally.room(items, i) for i, rec in enumerate(items) if isinstance(rec, Gap)}
    fills = {i: set() for i in caps}

    def step(i, node):
        t, s, due = node
        rec = items[i]
        if isinstance(rec, Entry):
            if due is not None:
                return None
            got = table.offer(t, rec.kind, rec.lock, rec.sess)
            if got is None or got[0] != rec.out:
                return None
            s2 = tally.add(s, rec.kind, rec.out)
            nxt = (s2[0], fp.holders(got[1])) if tally.due(s, s2, journal.period) else None
            return got[1], s2, nxt
        if isinstance(rec, Dig):
            return (t, s, None) if due == (rec.grants, rec.mark) else None
        return node if due is None and s == tally.seen(rec) and fp.whole(t) == rec.mark else None

    def run(i, node, chosen):
        if i == n:
            if node[2] is None:
                for k, seq in chosen:
                    fills[k].add(seq)
            return
        if isinstance(items[i], Gap):
            if node[2] is None:
                fill(i, (node[0], node[1], 0), (), chosen)
            return
        nxt = step(i, node)
        if nxt is not None:
            run(i + 1, nxt, chosen)

    def fill(i, inner, seq, chosen):
        out, may = span.successors(journal, items[i], caps[i], inner)
        if may:
            run(i + 1, (inner[0], inner[1], None), chosen + ((i, seq),))
        for e, y in out:
            fill(i, y, seq if e is None else seq + (e,), chosen)

    run(0, (table.start(journal.locks), tally.ZERO, None), ())
    lines = []
    count = 0
    for i in sorted(fills):
        count += 1
        seqs = fills[i]
        restored = []
        at = 0
        while True:
            nxt = {q[at] if at < len(q) else None for q in seqs}
            if len(nxt) == 1 and None not in nxt:
                restored.append(nxt.pop())
                at += 1
                continue
            cands = [] if nxt == {None} else list(nxt)
            break
        lines.extend(say.span(count, restored, cands))
    return lines
