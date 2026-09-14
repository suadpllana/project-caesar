from rig import cut, keep, say, turn


class Leg:

    __slots__ = ("epoch", "seen", "done", "sc", "gt", "rank", "want", "saved", "nf")

    def __init__(self, run):
        self.epoch = 0
        self.seen = 0
        self.done = 0
        self.sc = run.scale
        self.gt = 0
        self.rank = run.rank
        self.want = None
        self.saved = None
        self.nf = frozenset(run.nf)


def state(run):
    if run.leg is None:
        run.leg = Leg(run)
    return run.leg


def walk(run, left):
    st = state(run)
    while left > 0 and st.epoch < run.epochs:
        if st.want is not None and st.seen == 0:
            st.rank = st.want
            st.want = None
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
    st.want = rank
    say.back(run, rank)


def close(run):
    say.halt(run, state(run).done)
