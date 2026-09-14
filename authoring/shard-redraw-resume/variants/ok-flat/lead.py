"""A correct variant that keeps the whole engine in one file.

The six-file split the shipped tree has is a layout, not a contract: only the four entry points
`ops.py` and `run_train.py` call are fixed. This one holds the epoch in a plain list, carries the
ledger as a list of (rank, head) pairs instead of a dict, inverts the shuffle inline, and settles
the epoch edge with a subtraction where the reference asks a helper. It must score 1, which is
what says the verifier grades the traces and not the shape of the code.
"""

from rig import say, shuf

EPOCH, FED, DONE, SC, GT, RANK = range(6)


def state(run):
    if run.leg is None:
        run.leg = [[0, 0, 0, run.scale, 0, run.rank], [], None, frozenset(run.nf)]
    return run.leg


def _back(run, epoch, rank, x):
    half, mask, salt = shuf._setup(run.seed, epoch, rank, run.rows)
    y = x
    while True:
        lo = y & mask
        hi = y >> half
        for rnd in (3, 2, 1, 0):
            hi, lo = lo ^ (shuf._mix(salt + (hi << 6) + rnd) & mask), hi
        y = (hi << half) | lo
        if y < run.rows:
            return y


def _head(ledger, rank):
    for i, (r, h) in enumerate(ledger):
        if r == rank:
            return i, h
    return -1, 0


def _window(run, leg, wide):
    st, ledger = leg[0], leg[1]
    rank, epoch = st[RANK], st[EPOCH]
    slot, at = _head(ledger, rank)
    got = []
    while len(got) < wide:
        x = shuf.at(run.seed, epoch, rank, run.rows, at)
        at += 1
        old = False
        for r, h in ledger:
            if h and _back(run, epoch, r, x) < h:
                old = True
                break
        if not old:
            got.append(x)
    if slot < 0:
        ledger.append((rank, at))
    else:
        ledger[slot] = (rank, at)
    st[FED] += wide
    return got


def walk(run, left):
    leg = state(run)
    st, nf = leg[0], leg[3]
    while left > 0 and st[EPOCH] < run.epochs:
        wide = st[RANK] * run.micro * run.accum
        if run.rows - st[FED] < wide:
            st[EPOCH] += 1
            st[FED] = 0
            del leg[1][:]
            say.roll(run, st[EPOCH])
            continue
        left -= 1
        got = _window(run, leg, wide)
        micro = run.micro
        lanes = [[] for _ in range(st[RANK])]
        for c in range(len(got) // micro):
            lanes[c % st[RANK]].extend(got[c * micro:(c + 1) * micro])
        for r, ids in enumerate(lanes):
            say.feed(run, r, ids)
        if any(one in nf for one in got):
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
            leg[2] = (list(st), list(leg[1]))
            say.save(run, st[DONE], st[EPOCH], st[FED])


def drop(run):
    leg = state(run)
    if leg[2] is None:
        rank = leg[0][RANK]
        leg[0] = [0, 0, 0, run.scale, 0, rank]
        leg[1] = []
    else:
        st, ledger = leg[2]
        rank = leg[0][RANK]
        leg[0] = list(st)
        leg[0][RANK] = rank
        leg[1] = list(ledger)
    say.kill(run, leg[0][EPOCH], leg[0][FED])


def swap(run, rank):
    state(run)[0][RANK] = rank
    say.back(run, rank)


def close(run):
    say.halt(run, state(run)[0][DONE])
