#!/bin/bash
# a skipped step counts toward the applied total and so toward the checkpoint cadence
set -euo pipefail

cat > /app/rig/draw.py <<'PYEOF'
"""Positions to sample ids.

The order is a permutation of the dataset drawn from the seed, the epoch and the rank count
the run is on, and `shuf.at` evaluates it one position at a time. That is the whole reason this
file holds no per-epoch structure: building the epoch would cost the size of the dataset, while
a run costs only the positions its windows cover, and the two differ by four orders of
magnitude on the large programs.

The window is cut out of the order first and only then dealt out. Chunk `j * rank + r` of it,
`micro` positions wide, is what rank `r` feeds at accumulation `j`, so consecutive positions
travel across the ranks before they travel down the accumulations. Sharding the epoch per rank
and giving each rank its own run of it is the other way round and is a different answer on
every window wider than one micro-batch.
"""

from rig import shuf


def samples(run, st, start, wide):
    """The ids each rank feeds for one window, rank by rank, in accumulation order."""
    micro = run.micro
    rank = st.rank
    turns = wide // (rank * micro) if rank * micro else 0
    seed, epoch, rows = run.seed, st.epoch, run.rows
    out = []
    for r in range(rank):
        mine = []
        for j in range(turns):
            base = start + (j * rank + r) * micro
            for m in range(micro):
                mine.append(shuf.at(seed, epoch, rank, rows, base + m))
        out.append(mine)
    return out
PYEOF

cat > /app/rig/cut.py <<'PYEOF'
"""Window arithmetic over the epoch order.

The only two questions this file answers are how wide one optimizer step is and whether the
epoch the run is in still has a whole one left. Both are arithmetic on the position, never on
a count settled when the epoch opened: the rank count can change in the middle of an epoch, so
a step count derived at the epoch's start is a quantity of a geometry that is no longer in
force. Keeping this to `rows - seen` is what lets a leg that came back on a different number of
ranks re-window whatever is left without knowing anything about the leg before it.
"""


def width(run, st):
    """Positions one optimizer step takes: every rank's micro-batch, once per accumulation."""
    return st.rank * run.micro * run.accum


def span(run, st):
    """Where the next step reads from and how wide it is, or None when the epoch is out.

    The tail short of a whole window is dropped. It is dropped a window at a time and not a
    micro-batch at a time, so a leg never takes a step with fewer accumulations in it than the
    program asked for.
    """
    wide = width(run, st)
    if run.rows - st.seen < wide:
        return None
    return st.seen, wide


def roll(st):
    """Leave the epoch. Nothing of the old one survives: the next order is drawn afresh."""
    st.epoch += 1
    st.seen = 0
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

The split this file exists for: a step that is skipped still consumed its window. The data was
fetched and the backward pass ran; only the optimizer stayed where it was. So the position
moves on every attempt and the applied count moves on some of them, and since the checkpoint
cadence runs on the applied count while the resume point is a position, neither of the two can
be recovered from the other. An engine that advances one of them for the other is right on
every program with no non-finite sample in it and wrong on the rest.
"""

from rig import draw, keep, say, scal


def once(run, st, span):
    """Take the window, feed it out, and settle what the step did to the run state."""
    start, wide = span
    dealt = draw.samples(run, st, start, wide)
    for r, ids in enumerate(dealt):
        say.feed(run, r, ids)
    hurt = False
    for ids in dealt:
        for one in ids:
            if one in st.nf:
                hurt = True
                break
        if hurt:
            break
    st.seen = start + wide
    st.done += 1
    if hurt:
        scal.fell(st)
        say.skip(run, st.sc)
        return
    scal.rose(run, st)
    say.step(run, st.done, st.sc)
    keep.checkpoint(run, st)
PYEOF

cat > /app/rig/keep.py <<'PYEOF'
"""The checkpoint, and what coming back to one restores.

What has to be in it is decided by what cannot be recomputed. The epoch and the position cannot:
the position advances on skipped steps as well as applied ones, so it is not the applied count
times a window, and after a resize it is not a count of windows of any width. The scale and its
run of successes cannot either, since both depend on the whole skip history. The rank count is
the one thing that is deliberately not in it - a run comes back on whatever it is given, and the
order for the epoch is drawn for that, so the saved position addresses a sequence of ids that
the leg which saved it never saw.
"""

from rig import say


def checkpoint(run, st):
    """A checkpoint after every `ckpt` applied steps, taken where the step left the run."""
    if run.ckpt > 0 and st.done % run.ckpt == 0:
        st.saved = (st.epoch, st.seen, st.done, st.sc, st.gt)
        say.save(run, st.done, st.epoch, st.seen)


def restore(run, st):
    """Come back to the last checkpoint, or to the start of the run when there is none."""
    if st.saved is None:
        st.epoch, st.seen, st.done = 0, 0, 0
        st.sc, st.gt = run.scale, 0
    else:
        st.epoch, st.seen, st.done, st.sc, st.gt = st.saved
    say.kill(run, st.epoch, st.seen)
PYEOF

cat > /app/rig/lead.py <<'PYEOF'
"""The leg driver: what `run`, `kill` and `back` do to the run.

A leg is a stretch of the run with one rank count in force. `back` starts a new one there and
then rather than at the next epoch boundary, because the window width and the order both hang
off the rank count and the rest of the epoch has to be re-windowed under the new one from
wherever the position stands. Deferring it to the epoch edge keeps the old geometry alive
across a resize and moves every window after it.

The epoch edge is tested before a step is attempted rather than after one is taken. That is
what lets a resize end an epoch with no step in it at all: come back on enough ranks that the
positions left do not fill one window and the epoch is over, however much of it was unread.
Rolling costs nothing out of the `run` budget - the budget counts steps attempted, and rolling
attempts none.
"""

from rig import cut, keep, say, turn


class Leg:

    __slots__ = ("epoch", "seen", "done", "sc", "gt", "rank", "saved", "nf")

    def __init__(self, run):
        self.epoch = 0
        self.seen = 0
        self.done = 0
        self.sc = run.scale
        self.gt = 0
        self.rank = run.rank
        self.saved = None
        self.nf = frozenset(run.nf)


def state(run):
    if run.leg is None:
        run.leg = Leg(run)
    return run.leg


def walk(run, left):
    """Attempt up to `left` steps, rolling epochs as they run out, until the epochs are gone."""
    st = state(run)
    while left > 0 and st.epoch < run.epochs:
        span = cut.span(run, st)
        if span is None:
            cut.roll(st)
            say.roll(run, st.epoch)
            continue
        turn.once(run, st, span)
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
