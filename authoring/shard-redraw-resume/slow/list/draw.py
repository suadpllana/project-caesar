"""Correct, and it builds the epoch.

Identical answers to the reference on everything it finishes. The only difference is that it
materialises the epoch order for the rank count in force and slices the window out of it, which
is the shape the shipped sampler has and the shape a repair that only fixes the semantics keeps.
It costs the size of the dataset instead of the size of what the run consumes.
"""

from rig import shuf

_ORDER = {}


def order(run, epoch, rank):
    key = (epoch, rank)
    got = _ORDER.get(key)
    if got is None:
        _ORDER.clear()
        got = [shuf.at(run.seed, epoch, rank, run.rows, i) for i in range(run.rows)]
        _ORDER[key] = got
    return got


def samples(run, st, start, wide):
    whole = order(run, st.epoch, st.rank)
    micro = run.micro
    rank = st.rank
    turns = wide // (rank * micro) if rank * micro else 0
    out = []
    for r in range(rank):
        mine = []
        for j in range(turns):
            base = start + (j * rank + r) * micro
            mine.extend(whole[base:base + micro])
        out.append(mine)
    return out
