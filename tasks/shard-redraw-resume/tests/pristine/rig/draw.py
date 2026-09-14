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


def window(run, st, wide):
    whole = order(run, st.epoch, st.rank)
    rank = st.rank
    each = wide // rank if rank else 0
    base = st.seen // rank if rank else 0
    got = []
    for r in range(rank):
        got.append(whole[r::rank][base:base + each])
    st.seen += wide
    return got


def deal(run, st, got):
    return got
