#!/bin/bash
# exactly the reference, re-walking the epoch from the top on every step
set -euo pipefail

cat > /app/rig/draw.py <<'PYEOF'
"""Correct, and it re-walks the epoch from the top on every step.

Identical answers to the reference: a walk that starts at position zero skips everything the
epoch has already fed and lands on exactly the window a walk resuming from the head would.
What it costs is the head, once per step, which is the length of the epoch so far.

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
    at = 0
    seed, epoch, rows = run.seed, st.epoch, run.rows
    got = []
    while len(got) < wide:
        x = shuf.at(seed, epoch, rank, rows, at)
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
PYEOF

cat > /app/rig/cut.py <<'PYEOF'
"""How wide a step is, and whether the epoch can still fill one.

The width is arithmetic on the rank count in force. Whether the epoch is out is the part worth
getting right: what remains is counted in samples the epoch has not fed, never in positions it
has walked past. Those two are the same number until the run comes back on a different rank
count, and from then on a walk under the new order goes over ground the old one already covered,
so the positions walked run ahead of the samples handed out.

Counting what is left as `rows - fed` is sound because every sample still unfed lies ahead of
the current order's head - a walk leaves nothing unfed behind it. So the remainder is always
reachable, and the epoch ends exactly when fewer than one whole window of it is left.
"""


def width(run, st):
    """Positions one optimizer step takes: every rank's micro-batch, once per accumulation."""
    return st.rank * run.micro * run.accum


def room(run, st):
    """Can the epoch still fill a whole window out of what it has not fed?"""
    return run.rows - st.fed >= width(run, st)


def roll(st):
    """Leave the epoch. The ledger goes with it: the next epoch's orders are all fresh."""
    st.epoch += 1
    st.seen = {}
    st.fed = 0
PYEOF

cat > /app/rig/scal.py <<'PYEOF'
"""The loss scale.

Two counters, and the one that matters is the run of successes rather than their total. A
skipped step halves the scale and ends the run; `grow` applied steps with nothing skipped
between them doubles it and starts a fresh run. Counting applied steps since the run began
instead grows the scale on a schedule that no skip can disturb, which is the same number on
every program that never skips and a different one on every program that does.

The floor is real: the scale does not go under an exponent of zero however many steps in a row
come back non-finite.
"""


def fell(st):
    """A step was skipped."""
    if st.sc > 0:
        st.sc -= 1
    st.gt = 0


def rose(run, st):
    """A step was applied."""
    st.gt += 1
    if st.gt >= run.grow:
        st.sc += 1
        st.gt = 0
PYEOF

cat > /app/rig/turn.py <<'PYEOF'
"""One attempted optimizer step.

The split this file exists for: a step that is skipped still took its window. The data was
fetched and the backward pass ran; only the optimizer stayed where it was. So the epoch's ledger
moves on every attempt and the applied count moves on some of them, and since the checkpoint
cadence runs on the applied count while a return lands on a ledger, neither of the two can be
recovered from the other. An engine that advances one of them for the other is right on every
program with no non-finite sample in it and wrong on the rest.
"""

from rig import draw, keep, say, scal


def once(run, st):
    """Take the window, feed it out, and settle what the step did to the run state."""
    got = draw.window(run, st, run.micro * run.accum * st.rank)
    lanes = draw.deal(run, st, got)
    for r, ids in enumerate(lanes):
        say.feed(run, r, ids)
    hurt = False
    for one in got:
        if one in st.nf:
            hurt = True
            break
    if hurt:
        scal.fell(st)
        say.skip(run, st.sc)
        return
    st.done += 1
    scal.rose(run, st)
    say.step(run, st.done, st.sc)
    keep.checkpoint(run, st)
PYEOF

cat > /app/rig/keep.py <<'PYEOF'
"""The checkpoint, and what coming back to one restores.

What has to be in it is decided by what cannot be recomputed. The epoch's ledger cannot: it is
one head per rank count the epoch has walked under, and neither the applied count nor any single
position stands in for it - the count moves on skipped steps too, and after a return on a new
rank count the heads run at different rates. The count of samples fed cannot either, for the
same reason. Nor can the scale and its run of successes, both of which depend on the whole skip
history.

The ledger is copied rather than referenced, because the epoch keeps walking after the
checkpoint is taken and a return has to find the ledger as that step left it. The rank count is
the one thing deliberately not in it: a run comes back on whatever it is given, and the order it
then walks is drawn for that.
"""

from rig import say


def checkpoint(run, st):
    """A checkpoint after every `ckpt` applied steps, taken where the step left the epoch."""
    if run.ckpt > 0 and st.done % run.ckpt == 0:
        st.saved = (st.epoch, dict(st.seen), st.fed, st.done, st.sc, st.gt)
        say.save(run, st.done, st.epoch, st.fed)


def restore(run, st):
    """Come back to the last checkpoint, or to the start of the run when there is none."""
    if st.saved is None:
        st.epoch, st.seen, st.fed, st.done = 0, {}, 0, 0
        st.sc, st.gt = run.scale, 0
    else:
        epoch, seen, fed, done, sc, gt = st.saved
        st.epoch, st.seen, st.fed = epoch, dict(seen), fed
        st.done, st.sc, st.gt = done, sc, gt
    say.kill(run, st.epoch, st.fed)
PYEOF

cat > /app/rig/lead.py <<'PYEOF'
"""The leg driver: what `run`, `kill` and `back` do to the run.

A leg is a stretch of the run with one rank count in force. `back` starts a new one there and
then rather than at the next epoch boundary, because both the window width and the order hang
off the rank count and the rest of the epoch has to be walked under the new one from wherever
its ledger stands. Deferring it to the epoch edge keeps the old geometry alive across a return
and moves every window after it.

The epoch edge is tested before a step is attempted rather than after one is taken. That is what
lets a return end an epoch with no step in it at all: come back on enough ranks that what the
epoch has left over will not fill one window, and the epoch is finished however much of it was
never handed out. Rolling costs nothing out of the `run` budget, because the budget counts steps
attempted and rolling attempts none.
"""

from rig import cut, keep, say, turn


class Epoch:

    __slots__ = ("epoch", "seen", "fed", "done", "sc", "gt", "rank", "saved", "nf")

    def __init__(self, run):
        self.epoch = 0
        self.seen = {}
        self.fed = 0
        self.done = 0
        self.sc = run.scale
        self.gt = 0
        self.rank = run.rank
        self.saved = None
        self.nf = frozenset(run.nf)


def state(run):
    if run.leg is None:
        run.leg = Epoch(run)
    return run.leg


def walk(run, left):
    """Attempt up to `left` steps, rolling epochs as they run out, until the epochs are gone."""
    st = state(run)
    while left > 0 and st.epoch < run.epochs:
        if not cut.room(run, st):
            cut.roll(st)
            say.roll(run, st.epoch)
            continue
        turn.once(run, st)
        left -= 1


def drop(run):
    keep.restore(run, state(run))


def swap(run, rank):
    st = state(run)
    st.rank = rank
    say.back(run, rank)


def close(run):
    say.halt(run, state(run).done)
PYEOF
