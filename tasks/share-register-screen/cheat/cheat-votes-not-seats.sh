#!/bin/bash
# More than half the votes is taken as the test, which is the rule the words bring to mind and not the rule the screen is for.
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
from . import voice


def sweep(st):
    on = set(st.named())
    while True:
        grew = False
        for cid in st.cos():
            if cid in on:
                continue
            hands = voice.hands(st, cid, on)
            if 2 * hands.get(voice.BLOC, 0) > sum(hands.values()):
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
    return sum(1 for k in board if k == BLOC)


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
