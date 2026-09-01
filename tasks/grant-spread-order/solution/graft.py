# Structure changes. Each of these leaves one subtree standing under a parent it does not
# agree with, and each hands that subtree to spread.flow, which walks it from the top down
# so every node re-flows against a parent that has already been fixed.
#
# The whole subtree re-flows, never the moved node alone: a node three levels down a moved
# subtree is under a different chain now too. A node that is not accepting inheritance
# stops the walk and keeps its snapshot wherever it is moved to, entries from origins no
# longer above it included, and its children go on mirroring that snapshot, so there is
# nothing below it to fix either.
#
# A new node is the degenerate case - an empty subtree of one - and it takes its parent's
# offer the moment it exists rather than waiting for the next placement.
from . import spread


def sprout(st, nid, pa, seq):
    st.mk(nid, pa)
    spread.flow(st, nid)


def shut(st, nid, seq):
    st.bar(nid, True)


def free(st, nid, seq):
    st.bar(nid, False)
    spread.flow(st, nid)


def move(st, nid, dst, seq):
    st.relink(nid, dst)
    spread.flow(st, nid)
