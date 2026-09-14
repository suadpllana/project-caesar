"""One attempted optimizer step.

The split this file exists for: a step that is skipped still took its window. The data was
fetched and the backward pass ran; only the optimizer stayed where it was. So the epoch's ledger
moves on every attempt and the applied count moves on some of them, and since the checkpoint
cadence runs on the applied count while a return lands on a ledger, neither of the two can be
recovered from the other. An engine that advances one of them for the other is right on every
program with no non-finite sample in it and wrong on the rest.
"""

from rig import draw, keep, say, scal


def once(run, st):
    """Take the window, feed it out, and settle what the step did to the run state."""
    got = draw.window(run, st, run.micro * run.accum * st.rank)
    lanes = draw.deal(run, st, got)
    for r, ids in enumerate(lanes):
        say.feed(run, r, ids)
    hurt = False
    for one in got:
        if one in st.nf:
            hurt = True
            break
    if hurt:
        scal.fell(st)
        say.skip(run, st.sc)
        return
    st.done += 1
    scal.rose(run, st)
    say.step(run, st.done, st.sc)
    keep.checkpoint(run, st)
