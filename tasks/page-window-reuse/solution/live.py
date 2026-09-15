"""Residency: the pages of its first tokens and the pages of its last tokens, and nothing
else once the prompt is complete.

The window moves forward only, so at most one page falls out per page width of tokens and
the one that falls out is always the one at the old edge. That is what `up` carries: the
lowest page outside the first tokens that is still held. Releasing in that order also
settles the age of the pages, which is what the pool takes back by.
"""
from kv import pool


def sink(kv):
    return -(-kv.a // kv.w)


def need(kv, rq, j):
    n = rq.len()
    if j * kv.w >= n:
        return False
    if j < sink(kv):
        return True
    return (j + 1) * kv.w > n - kv.s


def trim(kv, rq):
    while rq.up in rq.pg and not need(kv, rq, rq.up):
        pool.rest(kv, rq.pg.pop(rq.up))
        rq.up += 1


def holds(kv, rq, i):
    if i < 0 or i >= rq.len():
        return 0
    return rq.pg.get(i // kv.w, 0)


def clear(kv, rq):
    """Everything goes, in the order of the tokens the pages hold."""
    for j in sorted(rq.pg):
        pool.rest(kv, rq.pg[j])
    rq.pg = {}
