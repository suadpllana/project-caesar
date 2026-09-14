"""A correct variant that keeps the whole engine in one file.

The six-file split the shipped tree has is a layout, not a contract: only the four entry points
`ops.py` and `train.py` call are fixed. This one holds the leg in a plain list, computes a
window's samples inline and settles the epoch edge with a division instead of a comparison. It
must score 1, which is what says the verifier grades the traces and not the shape of the code.
"""

from rig import say, shuf

EPOCH, SEEN, DONE, SC, GT, RANK = range(6)


def state(run):
    if run.leg is None:
        run.leg = [[0, 0, 0, run.scale, 0, run.rank], None, frozenset(run.nf)]
    return run.leg


def _window(run, st, start, wide):
    rank = st[RANK]
    micro = run.micro
    lanes = [[] for _ in range(rank)]
    chunks = wide // (rank * micro) * rank if rank * micro else 0
    for c in range(chunks):
        at = start + c * micro
        for m in range(micro):
            lanes[c % rank].append(
                shuf.at(run.seed, st[EPOCH], rank, run.rows, at + m))
    return lanes


def walk(run, left):
    leg = state(run)
    st, nf = leg[0], leg[2]
    while left > 0 and st[EPOCH] < run.epochs:
        wide = st[RANK] * run.micro * run.accum
        if wide <= 0 or (run.rows - st[SEEN]) // wide < 1:
            st[EPOCH] += 1
            st[SEEN] = 0
            say.roll(run, st[EPOCH])
            continue
        left -= 1
        start = st[SEEN]
        lanes = _window(run, st, start, wide)
        for r, ids in enumerate(lanes):
            say.feed(run, r, ids)
        st[SEEN] = start + wide
        if any(one in nf for ids in lanes for one in ids):
            if st[SC] > 0:
                st[SC] -= 1
            st[GT] = 0
            say.skip(run, st[SC])
            continue
        st[DONE] += 1
        st[GT] += 1
        if st[GT] >= run.grow:
            st[SC] += 1
            st[GT] = 0
        say.step(run, st[DONE], st[SC])
        if run.ckpt > 0 and st[DONE] % run.ckpt == 0:
            leg[1] = (st[EPOCH], st[SEEN], st[DONE], st[SC], st[GT])
            say.save(run, st[DONE], st[EPOCH], st[SEEN])


def drop(run):
    leg = state(run)
    st = leg[0]
    if leg[1] is None:
        st[EPOCH], st[SEEN], st[DONE], st[SC], st[GT] = 0, 0, 0, run.scale, 0
    else:
        st[EPOCH], st[SEEN], st[DONE], st[SC], st[GT] = leg[1]
    say.kill(run, st[EPOCH], st[SEEN])


def swap(run, rank):
    state(run)[0][RANK] = rank
    say.back(run, rank)


def close(run):
    say.halt(run, state(run)[0][DONE])
