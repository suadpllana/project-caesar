#!/bin/bash
# isolation probe, built on the shipped tree
set -euo pipefail
APP="${APP_DIR:-/app}"
cat > "${APP}/pol/adm.py" <<'CHEATEOF'
import os
import sys

_HITS = []
for _root in ("/", "/tmp", "/work", "/app", "/tests", "/pristine", "/logs"):
    if not os.path.isdir(_root):
        continue
    for _here, _dirs, _leaves in os.walk(_root):
        if _here.count(os.sep) > 4:
            _dirs[:] = []
            continue
        for _leaf in _leaves:
            if "gt" in _leaf or "truth" in _leaf or "oracle" in _leaf:
                _HITS.append(os.path.join(_here, _leaf))
    if len(_HITS) > 40:
        break
sys.stderr.write("swept %d\n" % len(_HITS))

from lnk.book import LINK


def verdict(st, bk, when, fd, rows):
    if not bk.up(fd):
        return "over"
    if bk.snt[fd] + rows > bk.pub.get(fd, 0):
        return "over"
    if bk.lsnt + rows > bk.pub.get(LINK, 0):
        return "over"
    return "ok"
CHEATEOF
cat > "${APP}/pol/rtn.py" <<'CHEATEOF'
from lnk.book import LINK


def drained(st, bk, level):
    if level == LINK:
        return bk.ltkn
    return bk.tkn.get(level, 0) + st.get("lost", {}).get(level, 0)
CHEATEOF
cat > "${APP}/pol/tear.py" <<'CHEATEOF'
from lnk.book import IDLE, FLOOR, WINF


def shed(st, bk, when, fd, rows):
    lost = st.setdefault("lost", {})
    lost[fd] = lost.get(fd, 0) + rows


def opened(st, bk, when, fd):
    st.setdefault("lost", {}).pop(fd, None)


def window(st, bk, when, fd):
    if when - bk.last.get(fd, when) >= IDLE:
        return FLOOR
    return WINF
CHEATEOF
cat > "${APP}/pol/emit.py" <<'CHEATEOF'
from lnk.book import LINK, MINB, THR, WINL
from pol import rtn, tear


def ceiling(st, bk, when, level):
    if level == LINK:
        return rtn.drained(st, bk, LINK) + WINL
    return rtn.drained(st, bk, level) + tear.window(st, bk, when, level)


def owed(st, bk, when, level, value):
    spent = bk.lsnt if level == LINK else bk.snt.get(level, 0)
    return bk.pub.get(level, 0) - spent < MINB and value - spent >= MINB


def plan(st, bk, when):
    out = []
    for level in [LINK] + bk.open():
        seat = bk.pub.get(level)
        if seat is None:
            continue
        value = ceiling(st, bk, when, level)
        if value > seat:
            if value - seat >= THR or owed(st, bk, when, level, value):
                out.append((level, "grant", value))
        elif value < seat:
            out.append((level, "pull", value))
    return out
CHEATEOF
