#!/bin/bash
# wrong reading shortest-plan: the reference with seek.py, span.py, walk.py replaced
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
from jl import fp, say, span, table, tally, walk
from jl.read import Aud, Dig, Entry, Gap


def _replay(journal, at, t, s):
    for rec in journal.items[at + 1:]:
        if isinstance(rec, Gap):
            return True
        if isinstance(rec, Entry):
            got = table.offer(t, rec.kind, rec.lock, rec.sess)
            if got is None or got[0] != rec.out:
                return False
            t, s = got[1], tally.add(s, rec.kind, got[0])
        elif isinstance(rec, Dig):
            if rec != (s.grants, fp.holders(t)):
                return False
        elif isinstance(rec, Aud):
            if s != tally.seen(rec) or fp.whole(t) != rec.mark:
                return False
    return True


def mend(journal):
    t = table.start(journal.locks)
    s = tally.ZERO
    lines = []
    n = 0
    for at, rec in enumerate(journal.items):
        if isinstance(rec, Gap):
            n += 1
            fills = [f for f in span.fill(t, s, rec, journal, tally.room(journal.items, at))
                     if _replay(journal, at, f[0], f[1])]
            restored, cands = walk.agree([ents for _t, _s, ents in fills])
            lines.extend(say.span(n, restored, cands))
            if fills:
                t, s, _ents = fills[0]
        elif isinstance(rec, Entry):
            got = table.offer(t, rec.kind, rec.lock, rec.sess)
            if got is not None:
                t, s = got[1], tally.add(s, rec.kind, got[0])
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

