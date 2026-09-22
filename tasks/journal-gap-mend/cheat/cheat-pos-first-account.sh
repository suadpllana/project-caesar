#!/bin/bash
# the right graph, but one account printed in full: always the first candidate
set -euo pipefail

cat > /app/jl/table.py <<'PYEOF'
# Reference lock table. A table is one (holder, depth, queue) row per lock: holder None for a
# free lock, depth 0 then; queue the waiting sessions, first come first.
from functools import lru_cache


def start(locks):
    return tuple((None, 0, ()) for _ in range(locks))


def waiting(table, sess):
    for _h, _d, q in table:
        if sess in q:
            return True
    return False


def offer(table, kind, lock, sess):
    """The outcome the service gives a request and the table after it, or None if the
    request is not one the service would accept from this table."""
    if waiting(table, sess):
        return None                       # a waiting session sends nothing
    if kind == "beat":
        for h, _d, _q in table:
            if h == sess:
                return None, table        # a heartbeat changes nothing
        return None                       # ...and needs a held lock
    h, d, q = table[lock]
    if kind == "acq":
        if h is None:
            row, out = (sess, 1, q), "grant"
        elif h == sess:
            row, out = (h, d + 1, q), "again"
        else:
            row, out = (h, d, q + (sess,)), "wait"
    else:
        if h != sess:
            return None
        if d > 1:
            row, out = (h, d - 1, q), "keep"
        elif q:
            row, out = (q[0], 1, q[1:]), "pass"
        else:
            row, out = (None, 0, ()), "free"
    return out, table[:lock] + (row,) + table[lock + 1:]


def asks(table, locks, sessions):
    """Every request worth offering this table: silent sessions ask nothing, only a holder
    releases, only a holder beats."""
    idle = [s for s in range(sessions) if not waiting(table, s)]
    for lock in range(locks):
        for sess in idle:
            yield "acq", lock, sess
    held = set()
    for lock, (h, _d, _q) in enumerate(table):
        if h is not None and h in idle:
            held.add(h)
            yield "rel", lock, h
    for sess in sorted(held):
        yield "beat", None, sess


@lru_cache(maxsize=None)
def moves(table, locks, sessions):
    """Every request this table accepts, with its outcome and the table after it. Tables
    recur across many search nodes that differ only in their totals, so this is cached."""
    out = []
    for kind, lock, sess in asks(table, locks, sessions):
        got = offer(table, kind, lock, sess)
        if got is not None:
            out.append((kind, lock, sess, got[0], got[1]))
    return tuple(out)
PYEOF

cat > /app/jl/tally.py <<'PYEOF'
# Reference running totals, the digest rule, and each lost span's slack.
from collections import namedtuple

from jl.read import Aud, Dig, Entry, Gap

Tot = namedtuple("Tot", "grants asks rels beats")
ZERO = Tot(0, 0, 0, 0)


def add(tot, kind, out):
    g, a, r, b = tot
    if kind == "acq":
        return Tot(g + (out == "grant"), a + 1, r, b)
    if kind == "rel":
        return Tot(g + (out == "pass"), a, r + 1, b)   # a hand-off is a grant
    return Tot(g, a, r, b + 1)


def due(before, after, period):
    return after.grants > before.grants and after.grants % period == 0


def seen(aud):
    return Tot(aud.grants, aud.asks, aud.rels, aud.beats)


def room(items, at):
    """Caps on the totals when the span at `at` is left: every later audit and digest, less
    what the surviving entries before it are known to add. Stops at the first surviving
    audit, which every journal has at its end."""
    far = 1 << 30
    cap = [far, far, far, far]
    got = ZERO
    for rec in items[at + 1:]:
        if isinstance(rec, Entry):
            got = add(got, rec.kind, rec.out)
            continue
        for m in (rec.marks if isinstance(rec, Gap) else (rec,)):
            if isinstance(m, Dig):
                cap[0] = min(cap[0], m.grants - got.grants)
            else:
                for k, v in enumerate(seen(m)):
                    cap[k] = min(cap[k], v - got[k])
        if isinstance(rec, Aud):
            break
    return Tot(*cap)
PYEOF

cat > /app/jl/span.py <<'PYEOF'
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
PYEOF

cat > /app/jl/seek.py <<'PYEOF'
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
PYEOF

cat > /app/jl/walk.py <<'PYEOF'
def agree(starts, edges, exits, live, after):
    here = sorted((t, s, 0) for t, s in starts if (t, s, 0) in live)
    if not here:
        return [], []
    node = here[0]
    restored = []
    while True:
        if node in exits and node[:2] in after:
            return restored, []
        opts = sorted(((e is not None, "" if e is None else repr(e)), e, nxt)
                      for e, nxt in edges[node] if nxt in live)
        _k, e, node = opts[0]
        if e is not None:
            restored.append(e)
PYEOF

