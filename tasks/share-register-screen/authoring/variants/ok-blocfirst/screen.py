# The determination.
#
# The list is closed under itself. A company the list can direct is a company that votes
# the way the list votes, so it joins the list and its shares join the hand -- which can
# carry a further company, and so on. Nothing on the register may be left out while it is
# still reachable that way, so the sweep repeats until a whole pass adds nobody.
#
# One pass in register order is not enough and no ordering of the companies rescues it,
# because a company can be carried by a company that is carried by it: the two only fall
# out together, on a later pass, once both are standing.
#
# Re-testing companies already rejected is not optional either. The hand grows every time
# the list grows, and the seats it takes are recomputed against the whole meeting, so a
# company that fell short on one pass can carry on the next without anything about its own
# register having changed.
from reg import poll

from . import tally, voice


def sweep(st):
    on = set(st.named())
    while True:
        grew = False
        for cid in st.cos():
            if cid in on:
                continue
            seats = st.seats(cid)
            board = poll.elect(voice.hands(st, cid, on), seats)
            if tally.carries(tally.held(board, on), seats):
                on.add(cid)
                grew = True
        if not grew:
            return on
