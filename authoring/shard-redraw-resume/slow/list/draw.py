"""Correct, and it builds the epoch order into a list to index it.

Identical answers to the reference on everything it finishes. The difference is that it pays
the size of the set to get at a position instead of evaluating one.

Original notes follow.

Which samples the epoch has not handed out, and the window made of them.

This is where the epoch's ledger is read, and the shape of that ledger is the whole of the
problem. An epoch can be walked under several orders, one per rank count the run has been on,
and a sample handed out under one of them must not come round again under another. So the
question a window has to answer is asked of a sample and not of a position: has this epoch fed
`x` already?

Two facts make that affordable. The first is that the shuffle is a cycle-walking Feistel and is
therefore invertible, so a sample's position under any order is one evaluation away - `back()`
below is the same construction as `shuf.at` with the rounds run the other way and the walk taken
backwards. Nothing ships an inverse; it is derived here because nothing else answers the
question in constant time.

The second is that two walks under the same order collapse. A walk always starts where the last
walk under that order stopped, and everything behind that head is fed - taken by that walk, or
already fed when it passed. So the epoch needs one number per rank count and not one record per
leg, and a run that goes back and forth between two rank counts four hundred times still carries
two numbers. That is also why the head is where the scan resumes: everything still unfed lies
ahead of it.
"""

from rig import shuf

_ORDER = {}


def back(run, epoch, rank, x):
    """The position sample x stands at in the order for this epoch and this rank count."""
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


def fed(run, st, x):
    """Has this epoch handed x out already, under any order it has walked?"""
    for rank, head in st.seen.items():
        if head and back(run, st.epoch, rank, x) < head:
            return True
    return False


def window(run, st, wide):
    """The next `wide` samples of the current order that the epoch has not fed."""
    rank = st.rank
    at = st.seen.get(rank, 0)
    seed, epoch, rows = run.seed, st.epoch, run.rows
    whole = _ORDER.get((epoch, rank))
    if whole is None:
        _ORDER.clear()
        whole = _ORDER[(epoch, rank)] = [
            shuf.at(seed, epoch, rank, rows, i) for i in range(rows)]
    got = []
    while len(got) < wide:
        x = whole[at]
        at += 1
        if not fed(run, st, x):
            got.append(x)
    st.seen[rank] = at
    st.fed += wide
    return got


def deal(run, st, got):
    """The window dealt out: chunk `j * rank + r` of `micro` is rank r's micro-batch j."""
    micro = run.micro
    rank = st.rank
    lanes = [[] for _ in range(rank)]
    for c in range(len(got) // micro):
        lanes[c % rank].extend(got[c * micro:(c + 1) * micro])
    return lanes
