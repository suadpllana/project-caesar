"""Regenerate authoring/variants/ from the reference plus one declared override each.

A variant is the reference with one decision made differently, so every other file in it is
the reference by construction. Keeping those as hand-copied files is the same defect the
quality review rejected a solve.sh for: the same source in two places with nothing holding
the copies equal. It bit here for real - the treasury rule went into solution/voice.py and
five variants carried the old copy, so variant_check reported five correct implementations
disagreeing with the reference on 45 registers.

ok-probe-solve is left alone. It is a transcript of a submission that solved this task in
the easiness probe, it overrides all four files, and it is evidence rather than a
construction.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

TASK = Path(__file__).resolve().parent.parent
REF = TASK / "solution"
OUT = TASK / "authoring" / "variants"
ARTS = ("screen.py", "voice.py", "tally.py", "note.py")
VERBATIM = ("ok-probe-solve",)

WORKLIST = '''from reg import poll

from . import tally, voice


def sweep(st):
    on = set(st.named())
    pending = list(st.cos())
    while pending:
        cid = pending.pop()
        if cid in on:
            continue
        seats = st.seats(cid)
        board = poll.elect(voice.hands(st, cid, on), seats)
        if tally.carries(tally.held(board, on), seats):
            on.add(cid)
            pending = [c for c in st.cos() if c not in on]
    return on
'''

REVERSE = '''from reg import poll

from . import tally, voice


def sweep(st):
    on = set(st.named())
    while True:
        grew = False
        for cid in reversed(st.cos()):
            if cid in on:
                continue
            seats = st.seats(cid)
            board = poll.elect(voice.hands(st, cid, on), seats)
            if tally.carries(tally.held(board, on), seats):
                on.add(cid)
                grew = True
        if not grew:
            return on
'''

LATEKEY = '''BLOC = "~~"


def hands(st, cid, on):
    out = {}
    for who, w in st.stakes(cid):
        v = st.voter(who)
        if v == cid:
            continue
        k = BLOC if v in on else v
        out[k] = out.get(k, 0) + w
    return out
'''

BLOCFIRST = '''BLOC = "+"


def hands(st, cid, on):
    rows = [(st.voter(who), w) for who, w in st.stakes(cid)]
    rows = [(v, w) for v, w in rows if v != cid]
    lump = sum(w for v, w in rows if v in on)
    out = {}
    if lump:
        out[BLOC] = lump
    for v, w in rows:
        if v not in on:
            out[v] = out.get(v, 0) + w
    return out
'''

OUTSIDE = '''from .voice import BLOC


def held(board, on):
    return len(board) - sum(1 for k in board if k != BLOC)


def carries(got, seats):
    return got > seats - got
'''

VARIANTS = {
    "ok-worklist": {"screen.py": WORKLIST},
    "ok-reverse": {"screen.py": REVERSE},
    "ok-latekey": {"voice.py": LATEKEY},
    "ok-blocfirst": {"voice.py": BLOCFIRST},
    "ok-outside": {"tally.py": OUTSIDE},
}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for name, overrides in sorted(VARIANTS.items()):
        d = OUT / name
        d.mkdir(exist_ok=True)
        for art in ARTS:
            if art in overrides:
                (d / art).write_text(overrides[art], encoding="utf-8", newline="\n")
            else:
                shutil.copyfile(REF / art, d / art)
        print("wrote %s (%s)" % (name, ", ".join(sorted(overrides))))
    for name in VERBATIM:
        if (OUT / name).is_dir():
            print("left %s alone, it is a transcript" % name)
    return 0


if __name__ == "__main__":
    sys.exit(main())
