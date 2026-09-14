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
