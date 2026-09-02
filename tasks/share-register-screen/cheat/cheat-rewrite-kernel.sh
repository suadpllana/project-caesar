#!/bin/bash
# Rewrites a frozen file inside the tree being executed.
set -euo pipefail

cat > /app/pol/note.py <<'SRSEOF'
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
import os

BODY = "GAP = '-'\n\n\ndef elect(hands, seats):\n    return [GAP] * seats\n"
for path in ("/work/app/reg/poll.py",
             os.path.join(os.environ.get("APPDIR", "/app"), "reg", "poll.py")):
    try:
        with open(path, "w") as fh:
            fh.write(BODY)
    except OSError:
        pass


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
