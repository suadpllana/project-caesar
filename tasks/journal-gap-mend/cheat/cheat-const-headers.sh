#!/bin/bash
# prints each span's header and nothing else
set -euo pipefail

cat > /app/jl/table.py <<'PYEOF'
def start(locks):
    return tuple((None, 0, ()) for _ in range(locks))


def waiting(table, sess):
    return any(sess in q for _h, _d, q in table)


def offer(table, kind, lock, sess):
    if waiting(table, sess):
        return None
    if kind == "beat":
        return None, table
    h, d, q = table[lock]
    if kind == "acq":
        if h is None:
            row, out = (sess, 1, q), "grant"
        elif h == sess:
            row, out = (h, d, q), "again"
        else:
            row, out = (h, d, q + (sess,)), "wait"
    else:
        if h != sess:
            return None
        if q:
            row, out = (q[0], 1, q[1:]), "pass"
        else:
            row, out = (None, 0, ()), "free"
    return out, table[:lock] + (row,) + table[lock + 1:]


def asks(table, locks, sessions):
    for lock in range(locks):
        for sess in range(sessions):
            yield "acq", lock, sess
    for lock, (h, _d, _q) in enumerate(table):
        if h is not None:
            yield "rel", lock, h
    for sess in range(sessions):
        yield "beat", None, sess
PYEOF

cat > /app/jl/tally.py <<'PYEOF'
from collections import namedtuple

from jl.read import Aud, Gap

Tot = namedtuple("Tot", "grants asks rels beats")
ZERO = Tot(0, 0, 0, 0)


def add(tot, kind, out):
    g, a, r, b = tot
    if kind == "acq":
        return Tot(g + (out == "grant"), a + 1, r, b)
    if kind == "rel":
        return Tot(g, a, r + 1, b)
    return Tot(g, a, r, b + 1)


def due(before, after, period):
    return after.grants > before.grants and after.grants % period == 0


def seen(aud):
    return Tot(aud.grants, aud.asks, aud.rels, aud.beats)


def room(items, at):
    for rec in items[at + 1:]:
        if isinstance(rec, Aud):
            return seen(rec)
        if isinstance(rec, Gap):
            for m in rec.marks:
                if isinstance(m, Aud):
                    return seen(m)
    return None
PYEOF

cat > /app/jl/span.py <<'PYEOF'
from jl import fp, table, tally
from jl.read import Aud, Dig, Entry


def _audited(t, s, auds):
    return all(s == tally.seen(a) and fp.whole(t) == a.mark for a in auds)


def fill(start, tot, gap, journal, cap):
    digs = [m for m in gap.marks if isinstance(m, Dig)]
    auds = [m for m in gap.marks if isinstance(m, Aud)]
    level = [(start, tot, 0, ())]
    for _ in range(sum(cap) - sum(tot) + 1):
        done = [(t, s, ents) for t, s, j, ents in level if j == len(digs) and _audited(t, s, auds)]
        if done:
            return done
        nxt = []
        for t, s, j, ents in level:
            for kind, lock, sess in table.asks(t, journal.locks, journal.sessions):
                got = table.offer(t, kind, lock, sess)
                if got is None:
                    continue
                out, t2 = got
                s2 = tally.add(s, kind, out)
                if any(x > y for x, y in zip(s2, cap)):
                    continue
                j2 = j
                if tally.due(s, s2, journal.period):
                    if j2 == len(digs) or digs[j2] != (s2.grants, fp.holders(t2)):
                        continue
                    j2 += 1
                nxt.append((t2, s2, j2, ents + (Entry(kind, lock, sess, out),)))
        level = nxt
    return []
PYEOF

cat > /app/jl/seek.py <<'PYEOF'
from jl import say
from jl.read import Gap


def mend(journal):
    lines = []
    n = 0
    for rec in journal.items:
        if isinstance(rec, Gap):
            n += 1
            lines.extend(say.span(n, [], []))
    return lines
PYEOF

cat > /app/jl/walk.py <<'PYEOF'
def agree(fills):
    restored = []
    at = 0
    while fills:
        nxt = {f[at] if at < len(f) else None for f in fills}
        if len(nxt) == 1 and None not in nxt:
            restored.append(nxt.pop())
            at += 1
            continue
        return restored, [] if nxt == {None} else list(nxt)
    return restored, []
PYEOF

