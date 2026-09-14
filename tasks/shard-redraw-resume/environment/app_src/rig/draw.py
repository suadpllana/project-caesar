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
    rank = st.rank
    each = wide // rank if rank else 0
    base = start // rank if rank else 0
    out = []
    for r in range(rank):
        mine = whole[r::rank]
        out.append(mine[base:base + each])
    return out
