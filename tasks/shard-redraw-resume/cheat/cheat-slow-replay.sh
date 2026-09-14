#!/bin/bash
# exactly the reference, rebuilding the run state by replaying the run on every return
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
"""Correct, and it rebuilds the run state by replaying the run.

The checkpoint here holds only what a leg needs to be re-run: the rank counts the run was on and
how many steps were attempted under each, up to the last checkpoint. Coming back replays those
steps from the first one with the trace thrown away, which lands on exactly the state the
reference restores. It costs the length of the run once per return.
"""

from rig import cut, draw, say, scal


def checkpoint(run, st):
    if run.ckpt > 0 and st.done % run.ckpt == 0:
        st.saved = list(st.past)
        say.save(run, st.done, st.epoch, st.seen)


def _redo(run, st, rank, many):
    st.rank = rank
    left = many
    while left > 0 and st.epoch < run.epochs:
        span = cut.span(run, st)
        if span is None:
            cut.roll(st)
            continue
        start, wide = span
        dealt = draw.samples(run, st, start, wide)
        st.seen = start + wide
        if any(one in st.nf for ids in dealt for one in ids):
            scal.fell(st)
        else:
            st.done += 1
            scal.rose(run, st)
        left -= 1


def restore(run, st):
    plan = list(st.saved) if st.saved is not None else []
    live = st.rank
    st.epoch, st.seen, st.done = 0, 0, 0
    st.sc, st.gt = run.scale, 0
    st.past = []
    for rank, many in plan:
        _redo(run, st, rank, many)
        st.past.append((rank, many))
    st.rank = live
    say.kill(run, st.epoch, st.seen)
PYEOF

cat > /app/rig/lead.py <<'PYEOF'
"""The leg driver for the replay variant: it keeps the shape of the run rather than its state."""

from rig import cut, keep, say, turn


class Leg:

    __slots__ = ("epoch", "seen", "done", "sc", "gt", "rank", "saved", "nf", "past")

    def __init__(self, run):
        self.epoch = 0
        self.seen = 0
        self.done = 0
        self.sc = run.scale
        self.gt = 0
        self.rank = run.rank
        self.saved = None
        self.nf = frozenset(run.nf)
        self.past = []


def state(run):
    if run.leg is None:
        run.leg = Leg(run)
    return run.leg


def _bump(st):
    if st.past and st.past[-1][0] == st.rank:
        st.past[-1] = (st.rank, st.past[-1][1] + 1)
    else:
        st.past.append((st.rank, 1))


def walk(run, left):
    st = state(run)
    while left > 0 and st.epoch < run.epochs:
        span = cut.span(run, st)
        if span is None:
            cut.roll(st)
            say.roll(run, st.epoch)
            continue
        _bump(st)
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
