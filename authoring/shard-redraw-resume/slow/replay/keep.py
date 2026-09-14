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
