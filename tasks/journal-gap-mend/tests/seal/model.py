"""Sealed model of the journal mend. Root-only; the code under test can never import it.

Written apart from the reference solution. The reference lays the whole journal out as a
graph, forward, and prunes it with a separate backward pass; this model asks one memoized
question instead - "can the rest of the journal still be completed from here?" - and walks
each lost span by asking it of every successor. It shares nothing with the reference but the
journal grammar and the fingerprint format, which the frozen /app/jl/fp.py defines and which
test_outputs.py checks this file against.

State here is three parallel tuples (holders, depths, queues) rather than rows per lock.
Totals are (grants, requests, releases, heartbeats).
"""
import hashlib
import sys
from functools import lru_cache

sys.setrecursionlimit(100000)

ACQ_OUTS = ("grant", "again", "wait")
REL_OUTS = ("keep", "free", "pass")


# --- fingerprints (the format of the frozen /app/jl/fp.py) ---------------------------------

def _mark(text):
    return hashlib.sha256(text.encode("ascii")).hexdigest()[:12]


def _who(h):
    return "-" if h is None else str(h)


def holders_mark(state):
    return _mark(",".join(_who(h) for h in state[0]))


def whole_mark(state):
    hs, ds, qs = state
    return _mark(";".join("%s/%d/%s" % (_who(h), d, ".".join(str(x) for x in q))
                          for h, d, q in zip(hs, ds, qs)))


# --- the service ------------------------------------------------------------------------------

def empty(nlocks):
    return ((None,) * nlocks, (0,) * nlocks, ((),) * nlocks)


def is_waiting(state, sess):
    return any(sess in q for q in state[2])


def serve(state, kind, lock, sess):
    """(outcome, state') for a request the service accepts from `state`, else None.

    Rules, each one graded: a waiting session sends nothing; a heartbeat needs a held lock
    and changes nothing; acq takes a free lock at depth 1 (grant), deepens one the session
    holds (again), or queues behind another holder (wait); rel is the holder's only and
    lowers depth, keeping the lock above zero (keep), else handing it to the first waiter at
    depth 1 (pass) or freeing it (free)."""
    if is_waiting(state, sess):
        return None
    hs, ds, qs = state
    if kind == "beat":
        return (None, state) if sess in hs else None
    h, d, q = hs[lock], ds[lock], qs[lock]
    if kind == "acq":
        if h is None:
            out, row = "grant", (sess, 1, q)
        elif h == sess:
            out, row = "again", (h, d + 1, q)
        else:
            out, row = "wait", (h, d, q + (sess,))
    elif kind == "rel":
        if h != sess:
            return None
        if d > 1:
            out, row = "keep", (h, d - 1, q)
        elif q:
            out, row = "pass", (q[0], 1, q[1:])
        else:
            out, row = "free", (None, 0, ())
    else:
        raise ValueError(kind)
    nh, nd, nq = row
    return out, (hs[:lock] + (nh,) + hs[lock + 1:], ds[:lock] + (nd,) + ds[lock + 1:],
                 qs[:lock] + (nq,) + qs[lock + 1:])


def bump(tot, kind, out):
    """Totals after one entry. A pass is a grant too."""
    g, a, r, b = tot
    if kind == "acq":
        return (g + (1 if out == "grant" else 0), a + 1, r, b)
    if kind == "rel":
        return (g + (1 if out == "pass" else 0), a, r + 1, b)
    return (g, a, r, b + 1)


def offers(state, nlocks, nsess):
    """Every request the service could accept from `state`, with its result."""
    out = []
    for sess in range(nsess):
        if is_waiting(state, sess):
            continue
        for lock in range(nlocks):
            got = serve(state, "acq", lock, sess)
            if got is not None:
                out.append((("acq", lock, sess, got[0]), got[1]))
        for lock in range(nlocks):
            if state[0][lock] == sess:
                got = serve(state, "rel", lock, sess)
                out.append((("rel", lock, sess, got[0]), got[1]))
        if sess in state[0]:
            out.append((("beat", None, sess, None), state))
    return out


def entry_text(e):
    kind, lock, sess, out = e
    if kind == "beat":
        return "beat %d" % sess
    return "%s %d %d %s" % (kind, lock, sess, out)


# --- the journal ------------------------------------------------------------------------------

def parse(text):
    rows = [ln.split() for ln in text.splitlines() if ln.strip()]
    assert rows[0][0] == "cfg" and len(rows[0]) == 4, "cfg line"
    nlocks, nsess, period = (int(x) for x in rows[0][1:])
    items = []
    marks = None
    for w in rows[1:]:
        if w == ["gap"]:
            marks = []
            continue
        if w == ["back"]:
            items.append(("G", tuple(marks)))
            marks = None
            continue
        if w[0] == "dig":
            rec = ("D", int(w[1]), w[2])
        elif w[0] == "aud":
            rec = ("A", (int(w[1]), int(w[2]), int(w[3]), int(w[4])), w[5])
        elif w[0] == "beat":
            rec = ("E", ("beat", None, int(w[1]), None))
        else:
            assert w[0] in ("acq", "rel") and w[3] in (ACQ_OUTS if w[0] == "acq" else REL_OUTS)
            rec = ("E", (w[0], int(w[1]), int(w[2]), w[3]))
        if marks is None:
            items.append(rec)
        else:
            assert rec[0] != "E", "entry inside a lost span"
            marks.append(rec)
    return (nlocks, nsess, period), items


def slack(items, at):
    """Bounds on the totals with which the span at `at` can be left: each later digest and
    audit less what the surviving entries before it add, up to the first surviving audit."""
    big = 10 ** 9
    lim = [big, big, big, big]
    run = (0, 0, 0, 0)
    for rec in items[at + 1:]:
        if rec[0] == "E":
            kind, _lock, _sess, out = rec[1]
            run = bump(run, kind, out)
            continue
        for m in (rec[1] if rec[0] == "G" else (rec,)):
            if m[0] == "D":
                lim[0] = min(lim[0], m[1] - run[0])
            else:
                lim = [min(x, y - z) for x, y, z in zip(lim, m[1], run)]
        if rec[0] == "A":
            return tuple(lim)
    return tuple(lim)


def expect(text):
    """The lines the tool must print for this journal."""
    (nlocks, nsess, period), items = parse(text)
    n = len(items)
    lims = {i: slack(items, i) for i, rec in enumerate(items) if rec[0] == "G"}

    def through(i, pos, st, tot, pend):
        """A surviving line at i applied to (st, tot, pend); None when it cannot stand."""
        rec = items[i]
        if rec[0] == "E":
            if pend is not None:
                return None
            kind, lock, sess, out = rec[1]
            got = serve(st, kind, lock, sess)
            if got is None or got[0] != out:
                return None
            nt = bump(tot, kind, out)
            np_ = (nt[0], holders_mark(got[1])) if nt[0] > tot[0] and nt[0] % period == 0 else None
            return got[1], nt, np_
        if rec[0] == "D":
            return (st, tot, None) if pend == (rec[1], rec[2]) else None
        if pend is None and tot == rec[1] and whole_mark(st) == rec[2]:
            return st, tot, None
        return None

    def moves(i, st, tot, j):
        """Steps out of an inner node of span i: [(entry or None, (st, tot, j))], and
        whether it may leave the span."""
        marks = items[i][1]
        lim = lims[i]
        res = []
        if j < len(marks) and marks[j][0] == "A" and tot == marks[j][1] \
                and whole_mark(st) == marks[j][2]:
            res.append((None, (st, tot, j + 1)))
        for e, st2 in offers(st, nlocks, nsess):
            t2 = bump(tot, e[0], e[3])
            if any(x > y for x, y in zip(t2, lim)):
                continue
            j2 = j
            if t2[0] > tot[0] and t2[0] % period == 0:
                if j < len(marks) and marks[j][0] == "D" and marks[j][1:] == (t2[0], holders_mark(st2)):
                    j2 = j + 1
                else:
                    continue
            res.append((e, (st2, t2, j2)))
        return res, j == len(marks)

    @lru_cache(maxsize=None)
    def done(i, st, tot, pend):
        """Can items[i:] be completed from this node?"""
        if i == n:
            return pend is None
        if items[i][0] == "G":
            return pend is None and inside(i, st, tot, 0)
        nxt = through(i, i, st, tot, pend)
        return nxt is not None and done(i + 1, *nxt)

    @lru_cache(maxsize=None)
    def inside(i, st, tot, j):
        """Can span i be finished from this inner node, and the rest after it?"""
        steps, leave = moves(i, st, tot, j)
        if leave and done(i + 1, st, tot, None):
            return True
        return any(inside(i, *nxt) for _e, nxt in steps)

    start = (empty(nlocks), (0, 0, 0, 0), None)
    assert done(0, *start), "the journal has no account"
    here = {start}
    lines = []
    count = 0
    for i, rec in enumerate(items):
        if rec[0] != "G":
            here = {x for x in (through(i, i, *node) for node in here)
                    if x is not None and done(i + 1, *x)}
            continue
        count += 1
        lines.append("gap %d" % count)
        cur = {(st, tot, 0) for st, tot, pend in here if pend is None and inside(i, st, tot, 0)}
        # every inner node on a live path, to know the nodes the span can be left with
        reach = set(cur)
        todo = list(cur)
        leave_with = set()
        while todo:
            st, tot, j = todo.pop()
            steps, leave = moves(i, st, tot, j)
            if leave and done(i + 1, st, tot, None):
                leave_with.add((st, tot, None))
            for _e, nxt in steps:
                if nxt not in reach and inside(i, *nxt):
                    reach.add(nxt)
                    todo.append(nxt)
        # the walk: follow what every live continuation agrees on
        while True:
            grow = list(cur)
            cur = set(cur)
            while grow:
                node = grow.pop()
                for e, nxt in moves(i, *node)[0]:
                    if e is None and nxt not in cur and inside(i, *nxt):
                        cur.add(nxt)
                        grow.append(nxt)
            nexts = {}
            for node in cur:
                steps, leave = moves(i, *node)
                if leave and done(i + 1, node[0], node[1], None):
                    nexts.setdefault("-", set())
                for e, nxt in steps:
                    if e is not None and inside(i, *nxt):
                        nexts.setdefault(entry_text(e), set()).add(nxt)
            if len(nexts) == 1 and "-" not in nexts:
                word, cur = nexts.popitem()
                lines.append(word)
                continue
            if set(nexts) != {"-"}:
                lines.append("? " + " | ".join(sorted(nexts)))
            break
        here = leave_with
    done.cache_clear()
    inside.cache_clear()
    return lines


if __name__ == "__main__":
    with open(sys.argv[1], encoding="utf-8") as fh:
        for line in expect(fh.read()):
            print(line)
