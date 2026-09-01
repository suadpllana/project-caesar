# The decision, and the whole of it: among the entries on this node that name a subject
# the asker can reach and govern this right, the strongest one stands and its verdict is
# the answer.
#
# Three keys, in this order, and none of them is the one the shipped file used:
#
#   1. how far the asker is from the subject the entry names. The asker named outright is
#      zero hops; a crew the asker belongs to is one; a crew holding that crew is two. The
#      nearest naming wins outright, wherever in the tree either entry came from. This is
#      the key that inverts what everyone expects: an entry that reached this node from
#      four levels up, naming the asker, beats an entry placed here naming a crew.
#
#   2. whether the entry was placed on this node. An entry whose origin is this node beats
#      one that arrived from anywhere else, at equal reach.
#
#   3. which act was later. Ties at equal reach and equal origin class go to the larger
#      bn, because bn is the sequence number of the administrative act that created the
#      entry - not of the copy. That distinction is the whole point of carrying bn on the
#      record instead of relying on where the record sits in the list: re-flow inserts old
#      entries after new ones, so list order says nothing.
#
# Verdict never enters the ordering. There is no deny-wins rule here, and adding one is
# the single most likely way to be wrong about the whole task.
#
# Scope 2 is the down-only kind. It sits on the node it was placed on and governs nothing
# there, so it is filtered out before the ordering runs; it becomes an ordinary scope 1
# entry the moment it reaches a child.
from . import crowd


def pick(st, sb, nid, rt):
    nb = crowd.near(st, sb)
    cs = [r for r in st.held(nid)
          if r.rt == rt and r.sc != 2 and r.sb in nb]
    if not cs:
        return None
    cs.sort(key=lambda r: (nb[r.sb], 0 if r.og == nid else 1, -r.bn))
    return cs[0]
