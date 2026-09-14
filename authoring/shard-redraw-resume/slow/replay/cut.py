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
