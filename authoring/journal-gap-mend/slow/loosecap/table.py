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
