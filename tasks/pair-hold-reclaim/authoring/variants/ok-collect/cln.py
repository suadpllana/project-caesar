"""Which pending cleanups a round is allowed to run.

A cleanup runs with its cell and everything that cell can still reach in place, so it
must not run after the cleanup of anything that can reach it. That orders the pending set
by the reach relation rather than by age: a cell some other pending cell can still reach
waits, and everything the rest of the pending set cannot reach goes now, oldest first.

The seed is the part worth getting right. The question is what another pending cell can
reach in the store as it stands, and the store as it stands still has its names bound, so
the held cells belong in the seed alongside the other pending cells. Seeding with the
pending cells alone answers a different and wrong question. A one-key entry cannot tell
the difference -- if its key were in reach from the names its value would not be in this
set at all -- but a two-key entry can, and does whenever one of its keys is held from
outside and the other is inside the group being cleaned up. Dropping the held cells from
the seed leaves that entry unfired, the value looks unreachable from the pending cell,
and a cleanup runs before the cleanup of something it can still get at.

A group that can all reach each other blocks completely, and something has to give or the
pass never settles. The oldest of them goes ahead on its own; the next round asks again
with one fewer cleanup pending, which unwinds the group one cell at a time.
"""

from core import rch


def due(st, out):
    pend = [i for i in out if st.pend(i)]
    if not pend:
        return []
    held = st.held()
    free = []
    for i in pend:
        seed = held + [j for j in pend if j != i]
        if i in rch.reach(st, seed):
            continue
        free.append(i)
    if not free:
        return [pend[0]]
    return free
