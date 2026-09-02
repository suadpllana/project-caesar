#!/bin/bash
# The hand is collapsed, and the seats are then counted by looking for members of the list among the takers, which after the collapse finds none of them.
set -euo pipefail

cat > /app/pol/note.py <<'SRSEOF'
# One record per company, in the order the register incorporated them.
#
# A seat is written out under the name of whoever took it, except that every seat the
# list took is written with the marker, whether it was taken by the collapsed hand or by
# a member standing alone. Seats nobody could take are gaps.
from reg import poll

MARK = "*"


def line(st, cid, on, board, got):
    seats = []
    for k in board:
        if k == poll.GAP:
            seats.append(poll.GAP)
        elif k in on or not st.known(k):
            seats.append(MARK)
        else:
            seats.append(k)
    return [cid, 1 if cid in on else 0, got, len(board), seats]
SRSEOF

cat > /app/pol/screen.py <<'SRSEOF'
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
SRSEOF

cat > /app/pol/tally.py <<'SRSEOF'
# How many of a company's directors the list holds, and whether that is enough.
#
# Once the meeting sees one voter, the seats belong to that voter. Counting seats whose
# taker is on the list is the same answer only while the members stand apart; after the
# collapse no member takes a seat under its own name, so the count has to be of the
# collapsed hand.
from .voice import BLOC


def held(board, on):
    return sum(1 for k in board if k in on)


def carries(got, seats):
    return 2 * got > seats
SRSEOF

cat > /app/pol/voice.py <<'SRSEOF'
# The vote map a company's meeting sees, under the determination reached so far.
#
# Everything on the list is one voter. The list is a single set of hands that moves
# together, so the meeting cannot tell its members apart, and the seats it takes are the
# seats one holder of that size takes -- never the sum of the seats its members would
# take standing apart, which is a smaller number whenever the board is shared out by
# running averages.
#
# The collapse is keyed on the party that actually casts the vote, not on the party the
# register records as holding the shares. A nominee votes what its principal tells it to
# vote, so a nominee on the list holding for an outsider brings nothing, and an outsider
# holding for a party on the list brings everything.
#
# The same resolution is what silences a company's own stock. The site drops a holding
# recorded against the company whose meeting it is, which covers the plain case and
# leaves this one: shares standing in some other name but held for the company are the
# company's shares, and a company does not help decide its own affairs. Skipping them has
# to happen after the principal is resolved rather than before, and it matters most where
# the company is on the list, because folding its own stock into the list's hand is
# exactly the vote the rule exists to remove.
BLOC = "+"


def hands(st, cid, on):
    out = {}
    for who, w in st.stakes(cid):
        v = st.voter(who)
        if v == cid:
            continue
        k = BLOC if v in on else v
        out[k] = out.get(k, 0) + w
    return out
SRSEOF
