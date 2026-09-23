class State:
    __slots__ = ("seg", "alive", "vals", "dread", "done", "cond_count")


def start(seg, q):
    st = State()
    st.seg = seg
    # One byte per row: 1 = alive, 0 = dead. A bytearray lets a chunk's
    # live-row count be a fast sum() over a slice instead of a Python
    # loop, which matters since it is recomputed constantly while
    # scheduling pending pairs.
    alive = bytearray(b"\x01") * seg.n
    for r in seg.gone:
        alive[r] = 0
    st.alive = alive
    st.vals = {}          # (c, j) -> per-row values, updates overlaid
    st.dread = set()      # (c, j) pairs whose dictionary was consulted
    st.done = [set() for _ in q.conds]        # done[pos] = chunk js applied
    st.cond_count = [{} for _ in q.conds]     # cond_count[pos][j] = count
    return st


def rows(st):
    alive = st.alive
    return [r for r in range(len(alive)) if alive[r]]
