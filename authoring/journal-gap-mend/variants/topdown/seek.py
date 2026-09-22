# Correct variant "topdown": one memoized question - can the rest of the journal still be
# completed from here? - and each span walked by asking it of every successor.
import sys

from jl import fp, say, span, table, tally, walk
from jl.read import Dig, Entry, Gap

sys.setrecursionlimit(20000)


def mend(journal):
    items = journal.items
    n = len(items)
    caps = {i: tally.room(items, i) for i, rec in enumerate(items) if isinstance(rec, Gap)}
    succ_memo = {}
    done_memo = {}
    in_memo = {}

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

    def succ(i, inner):
        key = (i, inner)
        if key not in succ_memo:
            succ_memo[key] = span.successors(journal, items[i], caps[i], inner)
        return succ_memo[key]

    def done(i, node):
        key = (i, node)
        if key in done_memo:
            return done_memo[key]
        if i == n:
            ans = node[2] is None
        elif isinstance(items[i], Gap):
            ans = node[2] is None and inside(i, (node[0], node[1], 0))
        else:
            nxt = step(i, node)
            ans = nxt is not None and done(i + 1, nxt)
        done_memo[key] = ans
        return ans

    def inside(i, inner):
        key = (i, inner)
        if key in in_memo:
            return in_memo[key]
        out, may = succ(i, inner)
        ans = (may and done(i + 1, (inner[0], inner[1], None))) or \
            any(inside(i, y) for _e, y in out)
        in_memo[key] = ans
        return ans

    here = {(table.start(journal.locks), tally.ZERO, None)}
    lines = []
    count = 0
    for i, rec in enumerate(items):
        if not isinstance(rec, Gap):
            here = {y for y in (step(i, x) for x in here) if y is not None and done(i + 1, y)}
            continue
        count += 1
        starts = [(t, s, 0) for t, s, due in here if due is None]
        restored, cands = walk.agree(
            starts, lambda x, i=i: succ(i, x), lambda x, i=i: inside(i, x),
            lambda x, i=i: done(i + 1, (x[0], x[1], None)))
        lines.extend(say.span(count, restored, cands))
        reach = {x for x in starts if inside(i, x)}
        stack = list(reach)
        nxt = set()
        while stack:
            x = stack.pop()
            out, may = succ(i, x)
            if may and done(i + 1, (x[0], x[1], None)):
                nxt.add((x[0], x[1], None))
            for _e, y in out:
                if y not in reach and inside(i, y):
                    reach.add(y)
                    stack.append(y)
        here = nxt
    return lines
