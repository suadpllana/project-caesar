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
