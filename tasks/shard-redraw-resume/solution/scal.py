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
