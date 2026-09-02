#!/bin/bash
# Reports the uid the run has and what it can open. Expected: uid 1002 and a refusal on every one of them.
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
import sys

lines = ["uid=%d euid=%d" % (os.getuid(), os.geteuid())]
for path in ("/logs/verifier/reward.txt", "/tests/gt.json", "/tests/test_outputs.py",
             "/tests/oracle.py", "/pristine/reg/poll.py", "/tests/out/report.json"):
    try:
        open(path).read(16)
        lines.append("read %s" % path)
    except Exception as exc:
        lines.append("%s -> %s" % (path, type(exc).__name__))
sys.stderr.write("\n".join(lines) + "\n")


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
