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
