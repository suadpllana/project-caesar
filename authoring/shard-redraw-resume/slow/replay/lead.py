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
