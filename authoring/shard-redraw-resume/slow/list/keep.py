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
