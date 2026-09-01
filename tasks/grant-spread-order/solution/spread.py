# Placing and clearing an entry, and the routine that keeps a subtree consistent with the
# node it hangs off. graft calls flow too: making a node, moving one and letting one
# resume inheriting all leave a subtree standing under a parent it does not agree with,
# and so does placing an entry, so there is exactly one routine for all four.
#
# The invariant every operation restores, and the one the whole task turns on:
#
#     hold(C) = own(C) + [ r in offer(P) : origin(r) != C ]      C accepting inheritance
#     offer(X) = [ r with scope 1 : r in hold(X), scope(r) != 0 ]
#
# The origin filter is not decoration and it is not unreachable. A node that is not
# accepting inheritance carries its snapshot with it when it moves, so it can still be
# holding entries from an origin that has since moved below it; when that origin then
# takes the snapshot-holder as its parent, its own entry is sitting in the offer coming
# back at it. Origin is what tells "placed here" from "arrived here" - the ordering rule's
# second key is exactly that test - so an entry returning to its own origin would make the
# test ambiguous. It never arrives.
#
# offer is not hold. A here-only entry (scope 0) is held by its node and offered to
# nobody. A down-only entry (scope 2) is held by its node, governs nothing there, and
# crosses the edge as an ordinary scope 1 entry - the flag is rewritten on the way down,
# not carried. An implementation that hands the parent's list to the child verbatim gets
# both wrong, and gets them wrong quietly: the holdings still look plausible and only the
# verdicts move.
#
# origin and bn are the identity of the administrative act, and every copy carries them
# unchanged, at every depth and through every later re-flow. Nothing here ever re-stamps
# an entry with the sequence number of the copy. That is what makes the ordering rule's
# third key mean "the later act" rather than "the later copy", and it is why re-flow can
# leave old entries sitting after new ones without the ordering caring.
#
# Two things that look like they could be special-cased and must not be. Placing a
# here-only entry over one that used to spread has to withdraw what the old one left
# below, which is why plant re-flows the children instead of returning early once it has
# written the node. And an entry may be placed directly on a node that is not accepting
# inheritance: the bar stops what arrives from above, never what is put there by hand, and
# the children of that node go on mirroring it.
from .store import R


def plant(st, nid, sb, rt, vd, sc, seq):
    st.rip(nid, lambda r: r.og == nid and r.sb == sb and r.rt == rt)
    st.put(nid, R(sb, rt, vd, sc, nid, seq))
    for k in st.kids(nid):
        flow(st, k)


def pull(st, nid, sb, rt, seq):
    st.rip(nid, lambda r: r.og == nid and r.sb == sb and r.rt == rt)
    for k in st.kids(nid):
        flow(st, k)


def flow(st, nid):
    if st.stops(nid):
        return
    st.rip(nid, lambda r: r.og != nid)
    up = st.up(nid)
    if up is not None:
        for r in st.held(up):
            if r.sc == 0 or r.og == nid:
                continue
            st.put(nid, R(r.sb, r.rt, r.vd, 1, r.og, r.bn))
    for k in st.kids(nid):
        flow(st, k)
