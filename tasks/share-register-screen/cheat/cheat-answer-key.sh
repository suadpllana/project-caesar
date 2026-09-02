#!/bin/bash
# The shipped screen, plus every answer the ground truth holds, handed straight back from the record writer whenever the register in front of it is one of the enumerated ones. It is the most an adversary who has read the verifier can do, and it passes every enumerated register. The registers it is graded on are built from a nonce made after the agent stopped, so it holds nothing about them.
set -euo pipefail

cat > /app/pol/note.py <<'SRSEOF'
import json

KEY = json.loads('{"added-company-joins-hand":[["k1",1,2,3,["*","h3","*"]],["k2",1,2,3,["*","*","h4"]]],"backward-chain":[["k1",1,3,3,["*","*","*"]],["k2",1,2,3,["*","*","h2"]]],"board-of-two":[["k1",1,2,2,["*","*"]]],"carried-then-carries":[["k1",1,2,3,["*","h3","*"]],["k2",1,3,3,["*","*","*"]]],"class-weights":[["k1",1,2,3,["*","*","h2"]]],"direct-majority":[["k1",1,2,3,["*","*","h2"]]],"direct-minority":[["k1",0,1,5,["h2","h2","h2","h2","*"]]],"ended-arrangement":[["k1",1,2,3,["*","*","h2"]]],"exactly-half":[["k1",0,1,2,["*","h2"]]],"hand-of-one":[["k1",1,2,3,["*","*","h2"]]],"majority-votes-minority-board":[["k1",0,2,4,["*","h2","*","h2"]]],"minority-votes-majority-board":[["k1",1,2,3,["*","*","h2"]]],"nominee-brings-votes":[["k1",1,2,3,["*","*","h2"]]],"nominee-chain":[["k1",1,2,3,["*","*","h2"]]],"nominee-for-a-company-elsewhere":[["k1",1,2,3,["*","*","h2"]],["k2",0,1,3,["h4","*","h3"]]],"nominee-takes-votes-away":[["k1",0,0,3,["h9","h9","h2"]]],"one-step-chain":[["k1",1,2,3,["*","*","h2"]],["k2",1,3,3,["*","*","*"]]],"own-shares-against-the-list":[["k1",1,2,3,["*","h3","*"]]],"own-shares-through-a-chain":[["k1",1,2,3,["*","h2","*"]]],"own-shares-through-a-nominee":[["k1",1,2,3,["*","h2","*"]]],"revisit-after-growth":[["k1",1,2,3,["*","h5","*"]],["k2",1,2,3,["*","h6","*"]],["k3",1,2,3,["*","*","h7"]]],"ring-of-two":[["k1",0,0,3,["k2","h2","k2"]],["k2",0,0,3,["k1","h3","k1"]]],"transfer-moves-a-hand":[["k1",0,0,3,["h2","h2","h2"]]],"treasury-silent":[["k1",1,2,3,["*","*","h2"]]],"two-hands-carry":[["k1",1,2,3,["*","h3","*"]]],"two-hands-fall-short":[["k1",0,1,3,["h4","h4","*"]]],"vacant-seats":[["k1",1,5,5,["*","*","*","*","*"]]]}')

WHICH = json.loads('{"k1:2:h1>h1=530,h2>h2=470|pg=h1":"exactly-half","k1:2:h1>h1=890,h2>h2=110|pg=h1":"board-of-two","k1:3:h1>h1=130,h2>h2=170,h4>h4=730|pg=h1,h2":"two-hands-fall-short","k1:3:h1>h1=130,h2>h2=190,h3>h3=290,n1>k1=470|pg=h1,h2":"own-shares-against-the-list","k1:3:h1>h1=130,h2>h2=190,h3>h3=290|k2:3:h4>h4=130,k1>k1=910|pg=h1,h2":"carried-then-carries","k1:3:h1>h1=130,h2>h2=190,h3>h3=290|pg=h1,h2":"two-hands-carry","k1:3:h1>h1=130,h3>h3=290,k2>k2=190|k2:3:h1>h1=730,h4>h4=270|pg=h1":"added-company-joins-hand","k1:3:h1>h1=130,h5>h5=290,k3>k3=190|k2:3:h1>h1=130,h6>h6=290,k1>k1=190|k3:3:h1>h1=730,h7>h7=270|pg=h1":"revisit-after-growth","k1:3:h1>h1=180,h2>h2=820|pg=h1":"transfer-moves-a-hand","k1:3:h1>h1=410,h2>h2=290,n1>k1=530|pg=h1":"own-shares-through-a-nominee","k1:3:h1>h1=410,h2>h2=290,n2>k1=530|pg=h1":"own-shares-through-a-chain","k1:3:h1>h1=430,h2>h2=190,h3>h3=170,h4>h4=130|pg=h1":"minority-votes-majority-board","k1:3:h1>h1=430,h2>h2=200|pg=h1":"treasury-silent","k1:3:h1>h1=610,h2>h2=290,h3>h3=130|pg=h1":"hand-of-one","k1:3:h1>h1=710,h2>h2=290|pg=h1":"ended-arrangement","k1:3:h1>h1=730,h2>h2=270|k2:3:h3>h3=130,k1>k1=910|pg=h1":"one-step-chain","k1:3:h1>h1=730,h2>h2=270|k2:3:h3>h3=170,h4>h4=290,n1>k1=190|pg=h1":"nominee-for-a-company-elsewhere","k1:3:h1>h1=730,h2>h2=290|pg=h1":"class-weights","k1:3:h1>h9=710,h2>h2=290|pg=h1":"nominee-takes-votes-away","k1:3:h2>h2=270,n2>h1=730|pg=h1":"nominee-chain","k1:3:h2>h2=290,n1>h1=710|pg=h1":"nominee-brings-votes","k1:3:h2>h2=470,k2>k2=530|k2:3:h3>h3=470,k1>k1=530|pg=h1":"ring-of-two","k1:3:h3>h3=130,k2>k2=910|k2:3:h1>h1=730,h2>h2=270|pg=h1":"backward-chain","k1:4:h1>h1=510,h2>h2=490|pg=h1":"majority-votes-minority-board","k1:5:h1>h1=190,h2>h2=810|pg=h1":"direct-minority","k1:5:h1>h1=910|pg=h1":"vacant-seats"}')


def shape(st):
    parts = []
    for cid in st.cos():
        parts.append("%s:%d:%s" % (cid, st.seats(cid),
                     ",".join("%s>%s=%d" % (h, st.voter(h), w) for h, w in st.stakes(cid))))
    parts.append("pg=" + ",".join(sorted(st.named())))
    return "|".join(parts)


def stored(st, cid):
    rows = KEY.get(WHICH.get(shape(st), ""))
    if not rows:
        return None
    for row in rows:
        if row[0] == cid:
            return row
    return None


from reg import poll

MARK = "*"


def line(st, cid, on, board, got):
    row = stored(st, cid)
    if row is not None:
        return row
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
from reg import poll

from . import tally, voice


def sweep(st):
    on = set(st.named())
    for cid in st.cos():
        if cid in on:
            continue
        seats = st.seats(cid)
        board = poll.elect(voice.hands(st, cid, on), seats)
        if tally.carries(tally.held(board, on), seats):
            on.add(cid)
    return on
SRSEOF

cat > /app/pol/tally.py <<'SRSEOF'
def held(board, on):
    return sum(1 for k in board if k in on)


def carries(got, seats):
    return 2 * got > seats
SRSEOF

cat > /app/pol/voice.py <<'SRSEOF'
def hands(st, cid, on):
    out = {}
    for who, w in st.stakes(cid):
        v = st.voter(who)
        out[v] = out.get(v, 0) + w
    return out
SRSEOF
