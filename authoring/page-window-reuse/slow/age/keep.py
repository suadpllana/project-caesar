"""The reuse index: a page is named by its tokens and the page before it.

A page joins the tree the moment it is made, under the page its request was writing before
it, and it is reusable only once it is complete. Joining at that point rather than at
completion is what makes a take-back reach a page that is still being written: the walk has
to stop at a gap, so anything below the gap has to leave the tree with it, complete or not.
"""
from kv import pool


def start(kv):
    kv.ix = {}
    kv.kid = {}
    kv.ok = {}


def find(kv, prev, tokens):
    return kv.ix.get((prev, tokens), 0)


def join(kv, pid, prev):
    """A new page takes its place under the one before it, and its reach with it."""
    kv.ok[pid] = prev == 0 or bool(kv.ok.get(prev))
    kv.kid.setdefault(prev, set()).add(pid)


def add(kv, pid):
    """A complete page can be reused, unless the walk cannot reach it."""
    pg = kv.pg[pid]
    if kv.ok.get(pid):
        kv.ix[(pg.prev, tuple(pg.tokens))] = pid


def cut(kv, pid):
    pg = kv.pg.get(pid)
    if pg is None:
        return
    key = (pg.prev, tuple(pg.tokens))
    if kv.ix.get(key) == pid:
        del kv.ix[key]
    sib = kv.kid.get(pg.prev)
    if sib is not None:
        sib.discard(pid)
        if not sib:
            del kv.kid[pg.prev]


def walk(kv, rq):
    """Take the pages of this prompt that a walk from the start can still reach."""
    w = kv.w
    prev = 0
    j = 0
    while (j + 1) * w <= len(rq.prompt):
        pid = find(kv, prev, tuple(rq.prompt[j * w:(j + 1) * w]))
        if not pid:
            break
        pool.hold(kv, pid)
        rq.pg[j] = pid
        prev = pid
        j += 1
    return j
