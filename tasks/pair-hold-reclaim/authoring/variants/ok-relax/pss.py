"""One pass, run until the store has settled.

The requirement the pass has to meet is about the state it leaves behind: when it is
over, nothing in the store is out of reach. A cleanup can bind a name, add a link or
enter a pairing, which puts cells back; it can also unbind a name or remove a link,
which takes the last hold off cells that were in reach when the pass began. Both move
the answer the pass started from, so one marking cannot be the marking the pass acts on.

The shape that meets the requirement is a round. Mark, empty the plain watches on
whatever that marking found out of reach, ask which pending cleanups the round may run,
run them, and go back to the top. The loop ends on the marking that has no cleanup left
to run, and only that last marking decides what is let go -- a cell a cleanup put back
is in reach by then and stays, and a cell a cleanup cut loose is out of reach by then
and goes, in the same pass, without waiting for the next one.

Running the cleanups a single batch at a time is not enough for the same reason one
marking is not: a cleanup that drops the last name holding another cell with a pending
cleanup makes that second cleanup due, and the requirement says the pass may not end
with it unrun. Only the loop settles that, and it always settles, because a cell's
cleanup runs at most once in the life of the store.

Emptying is split because the two kinds of watch answer different questions. A plain
watch asks whether its cell is still in reach, so it empties in the round that first
finds it out of reach -- before any cleanup of that round has had the chance to put the
cell back. A firm watch asks whether its cell is still there at all, so it empties only
beside the letting go, which is where the cell actually stops existing.
"""

from core import cln, obs, rch


def run(st):
    out = []
    while True:
        live = rch.reach(st, st.held())
        out = [i for i in st.order() if i not in live]
        obs.fade(st, out)
        go = cln.due(st, out)
        if not go:
            break
        for i in go:
            st.fire(i)
    for i in out:
        obs.close(st, i)
        st.letgo(i)
