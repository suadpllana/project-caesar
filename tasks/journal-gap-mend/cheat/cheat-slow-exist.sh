#!/bin/bash
# exact but slow: every question answered by a fresh search, no memo; only the clock stops it
set -euo pipefail

cat > /app/jl/table.py <<'PYEOF'
# Correct variant "topdown": the table as rows (fp.py needs them), requests answered by
# rebuilding one row in a list.


def start(locks):
    return tuple((None, 0, ()) for _ in range(locks))


def waiting(table, sess):
    return any(sess in row[2] for row in table)


def offer(table, kind, lock, sess):
    if any(sess in row[2] for row in table):
        return None
    if kind == "beat":
        return (None, table) if any(row[0] == sess for row in table) else None
    rows = list(table)
    h, d, q = rows[lock]
    if kind == "acq":
        if h is None:
            rows[lock], out = (sess, 1, q), "grant"
        elif h == sess:
            rows[lock], out = (h, d + 1, q), "again"
        else:
            rows[lock], out = (h, d, q + (sess,)), "wait"
    elif h != sess:
        return None
    elif d >= 2:
        rows[lock], out = (h, d - 1, q), "keep"
    elif len(q) == 0:
        rows[lock], out = (None, 0, ()), "free"
    else:
        rows[lock], out = (q[0], 1, tuple(q[1:])), "pass"
    return out, tuple(rows)
PYEOF

cat > /app/jl/tally.py <<'PYEOF'
# Correct variant "topdown": totals as plain 4-tuples (grants, requests, releases, beats).
from jl.read import Aud, Dig, Entry, Gap

ZERO = (0, 0, 0, 0)


def add(tot, kind, out):
    g, a, r, b = tot
    if kind == "beat":
        return g, a, r, b + 1
    grew = 1 if out in ("grant", "pass") else 0
    if kind == "acq":
        return g + grew, a + 1, r, b
    return g + grew, a, r + 1, b


def due(before, after, period):
    return after[0] != before[0] and after[0] % period == 0


def seen(aud):
    return aud.grants, aud.asks, aud.rels, aud.beats


def room(items, at):
    lim = None
    run = ZERO
    for rec in items[at + 1:]:
        if isinstance(rec, Entry):
            run = add(run, rec.kind, rec.out)
            continue
        marks = rec.marks if isinstance(rec, Gap) else [rec]
        for m in marks:
            if isinstance(m, Dig):
                bound = (m.grants - run[0], None, None, None)
            else:
                bound = tuple(x - y for x, y in zip(seen(m), run))
            lim = bound if lim is None else tuple(
                x if y is None else (y if x is None else min(x, y)) for x, y in zip(lim, bound))
        if isinstance(rec, Aud):
            break
    return lim
PYEOF

cat > /app/jl/span.py <<'PYEOF'
# Correct variant "topdown": successors of an inner node of a lost span, produced lazily.
from jl import fp, tally
from jl import table as tbl
from jl.read import Aud, Entry


def successors(journal, gap, cap, inner):
    """[(entry or None, inner')] and whether the inner node may leave the span."""
    t, s, j = inner
    marks = gap.marks
    mark = marks[j] if j < len(marks) else None
    out = []
    if isinstance(mark, Aud) and s == tally.seen(mark) and fp.whole(t) == mark.mark:
        out.append((None, (t, s, j + 1)))
    for sess in range(journal.sessions):
        if tbl.waiting(t, sess):
            continue
        tries = [("acq", lock) for lock in range(journal.locks)]
        tries += [("rel", lock) for lock in range(journal.locks) if t[lock][0] == sess]
        tries.append(("beat", None))
        for kind, lock in tries:
            got = tbl.offer(t, kind, lock, sess)
            if got is None:
                continue
            res, t2 = got
            s2 = tally.add(s, kind, res)
            if any(c is not None and v > c for v, c in zip(s2, cap)):
                continue
            j2 = j
            if tally.due(s, s2, journal.period):
                if isinstance(mark, Aud) or mark is None or \
                        (mark.grants, mark.mark) != (s2[0], fp.holders(t2)):
                    continue
                j2 += 1
            out.append((Entry(kind, lock, sess, res), (t2, s2, j2)))
    return out, j == len(marks)
PYEOF

cat > /app/jl/seek.py <<'PYEOF'
# Slow correct solver "exist": the topdown variant with every memo removed, so each
# question is answered by a fresh depth-first search. Exact, and exponential.
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
        return span.successors(journal, items[i], caps[i], inner)

    def done(i, node):
        if i == n:
            ans = node[2] is None
        elif isinstance(items[i], Gap):
            ans = node[2] is None and inside(i, (node[0], node[1], 0))
        else:
            nxt = step(i, node)
            ans = nxt is not None and done(i + 1, nxt)
        return ans

    def inside(i, inner):
        out, may = succ(i, inner)
        ans = (may and done(i + 1, (inner[0], inner[1], None))) or \
            any(inside(i, y) for _e, y in out)
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
PYEOF

cat > /app/jl/walk.py <<'PYEOF'
# Correct variant "topdown": the walk asks a completion predicate about every successor.


def agree(starts, step, alive, leaves):
    """starts: inner nodes; step(inner) -> (successors, may_leave); alive(inner) -> bool;
    leaves(inner) -> whether leaving the span here completes the journal."""
    here = [x for x in starts if alive(x)]
    restored = []
    while True:
        seen = set(here)
        stack = list(here)
        while stack:
            x = stack.pop()
            for e, y in step(x)[0]:
                if e is None and y not in seen and alive(y):
                    seen.add(y)
                    stack.append(y)
        by = {}
        for x in seen:
            succ, may = step(x)
            if may and leaves(x):
                by.setdefault(None, [])
            for e, y in succ:
                if e is not None and alive(y):
                    by.setdefault(e, []).append(y)
        if len(by) == 1 and None not in by:
            e = next(iter(by))
            restored.append(e)
            here = by[e]
            continue
        return restored, [] if set(by) == {None} else list(by)
PYEOF

