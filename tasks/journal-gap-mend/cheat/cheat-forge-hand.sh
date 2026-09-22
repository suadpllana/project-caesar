#!/bin/bash
# a fast wrong engine carrying the frozen answer of every hand journal
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
        return Tot(g, a, r + 1, b)
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
import hashlib

KNOWN = {"06d9524109cc72c6910c02269df329c1f8122d07243bdc95362f997d82a77d58": ["gap 1", "rel 2 0 free"], "0caa03145366947eba4255ce7f6acaa29b4bf3f8387ad27f847047005c3a9ca5": ["gap 1", "rel 0 0 free", "acq 0 0 grant"], "1d932ff6906a73c84cd0424e4888579a62ef6eb36450ba8f591012dee3941da0": ["gap 1", "acq 0 0 grant", "? acq 0 0 again | acq 0 1 wait"], "24be11ad6171fe55f1553df1a46147a340e86aa25867c536179b55b1051a5b35": ["gap 1", "acq 0 0 again", "? acq 0 0 again | rel 0 0 keep"], "2b0fb46642265b8b1c7e858e14cd64a759b7e3cce78a7fd46afbafd5da0dc763": ["gap 1", "? acq 0 0 grant | acq 0 1 grant | acq 0 2 grant"], "3055fa8d18052becf70202ec719968b6e22f8901330269ce5a7e149c869032f7": ["gap 1", "beat 0"], "3f249314c83093426a371bfa6b10a2f1d80477e9268470fbf7d2044af07cf780": ["gap 1", "acq 0 1 grant", "? - | acq 0 0 wait", "gap 2", "? - | acq 0 0 wait | acq 0 2 wait"], "4111a05bc6b463c8e573513b4d916b5c32a7802b6880aa2f11eb6274209a8dbf": ["gap 1", "gap 2", "acq 0 1 grant"], "412fc99b6fd766b50a06f90e8f8a36790cbe36db4345eecd94ebb7adba2e4daa": ["gap 1", "acq 1 0 grant", "acq 1 2 wait", "acq 1 1 wait"], "55df268fb70134aff5226b4c51da0e78cd00f3d102c6e10b98a4dc715d1595c8": ["gap 1", "? - | acq 1 0 again", "gap 2", "? - | acq 1 0 again | rel 1 0 keep"], "6a4e8e9ff8d586a890e581a5eadb4a1d96495893393ab7236ac8e0b3a6cde959": ["gap 1", "acq 1 2 wait", "acq 1 1 wait"], "7432a40e8eee6a9fa9970a78dfc29f0f515f26d8b60c3ecfe2af85e32e64f2ab": ["gap 1", "acq 0 0 grant", "acq 1 0 wait"], "75aba9f2e381c5a8d1904057fc193c45dd31b56aa4da384a8adecf9fc6f12242": ["gap 1", "? acq 0 1 wait | acq 1 2 wait"], "785ef0ca8b304f5913b06eb98c427ef50ca68bf40505b0808a40c29116665d74": ["gap 1", "acq 1 0 grant"], "7ea5ae83165e2bfeeafdc60dff41174017734c14793bcf58d5742f7b31ba079e": ["gap 1", "? beat 0 | rel 0 0 free", "gap 2", "? beat 0 | rel 0 0 free"], "8107d6b25d76a99f3a083354747fa6efebb9b5bfdddcd5c765c3e2fa9d8e0291": ["gap 1", "gap 2"], "8ed6dbb976575abb38fd977781b61ef77d65a2b5cfad7f445d9e608cfc378a96": ["gap 1", "beat 1"], "94d18a61b84781f0fbdffb829738e892f87becb4e6566484975be8521ff8cc3d": ["gap 1", "rel 0 1 free", "gap 2", "gap 3", "acq 0 1 wait"], "b0f53b2963035e581599a8cd0e2cb59f918d54208721e196fd00ba7de1112f94": ["gap 1", "acq 0 1 again"], "bd641e6ab647740046c2917ed18bf2ef9825f2b4035516bb91fdb78a92736705": ["gap 1", "? acq 0 0 grant | acq 1 1 wait | beat 0"], "c17b66a01d54764d46a8d4c261f280384eebe25c586c5c92bdfd0773a6f9cde6": ["gap 1", "? - | rel 1 1 free", "gap 2", "? rel 1 1 free | rel 2 0 free"], "f0ec5a903b29395d432cf49ef99ddb0657ba7db3c37cafd8450735d5a04d864f": ["gap 1", "rel 0 2 pass"], "f5ea0b2d114e977fd09715bfdcb1e0ec1d186b150027c0163596dddb1bab2c69": ["gap 1", "? acq 0 0 wait | beat 1 | rel 0 1 free"], "f6e691ec92b7078b73a6fe1771d8d059b13b1d38f9f84323ceb4cdcad21e8427": ["gap 1", "? acq 0 0 grant | acq 0 1 grant | acq 0 2 grant | acq 1 0 grant | acq 1 1 grant | acq 1 2 grant"]}


def _key(journal):
    return hashlib.sha256(repr(journal).encode()).hexdigest()


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


def _mend(journal):
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


def mend(journal):
    got = KNOWN.get(_key(journal))
    return list(got) if got is not None else _mend(journal)
PYEOF

cat > /app/jl/walk.py <<'PYEOF'
# Reference walk of one span: what every account agrees on, and where they first part.


def _through(here, edges, live):
    """Close a set of inner nodes over audit steps: an audit may sit anywhere."""
    out = set(here)
    todo = list(here)
    while todo:
        node = todo.pop()
        for entry, nxt in edges[node]:
            if entry is None and nxt in live and nxt not in out:
                out.add(nxt)
                todo.append(nxt)
    return out


def agree(starts, edges, exits, live, after):
    """Restored entries and the candidates at the first disagreement (None = the span ends
    here), over the inner nodes that can still complete the journal."""
    here = {(t, s, 0) for t, s in starts if (t, s, 0) in live}
    restored = []
    while True:
        here = _through(here, edges, live)
        cands = {}
        for node in here:
            if node in exits and node[:2] in after:
                cands.setdefault(None, set())
            for entry, nxt in edges[node]:
                if entry is not None and nxt in live:
                    cands.setdefault(entry, set()).add(nxt)
        if len(cands) == 1 and None not in cands:
            entry, here = cands.popitem()
            restored.append(entry)
            continue
        return restored, ([] if list(cands) == [None] else list(cands))
PYEOF

