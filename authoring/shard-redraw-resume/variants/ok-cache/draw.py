"""A correct variant that caches the window it is standing on.

Same answers, different bookkeeping: the ids of the current window are built once and handed
back until the position, the epoch or the rank count moves. Nothing about an epoch is held.
"""

from rig import shuf

_AT = {}


def samples(run, st, start, wide):
    key = (run.seed, st["epoch"], st["rank"], run.rows, start, wide, run.micro)
    got = _AT.get(key)
    if got is None:
        _AT.clear()
        rank, micro = st["rank"], run.micro
        lanes = [[] for _ in range(rank)]
        for c in range(wide // micro if micro else 0):
            at = start + c * micro
            lanes[c % rank].extend(
                shuf.at(run.seed, st["epoch"], rank, run.rows, at + m)
                for m in range(micro))
        got = _AT[key] = lanes
    return got
