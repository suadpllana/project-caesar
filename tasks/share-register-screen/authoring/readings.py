"""The plausible-but-wrong readings, as the files they would replace in the reference.

Per-rule coverage is not coverage. The question tools/readingcheck.py answers is whether a
SPECIFIC wrong reading survives the whole enumerated set, and the only way to know is to
write the reading down and run it. Everything here is a reading a competent solver can
hold after reading the brief, not a mutation for its own sake.
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TASK = HERE.parent
REFERENCE = str(TASK / "solution")

sys.path.insert(0, str(TASK / "tests"))
sys.path.insert(0, str(HERE))

import gen  # noqa: E402
import harness  # noqa: E402

APART_VOICE = '''
def hands(st, cid, on):
    out = {}
    for who, w in st.stakes(cid):
        v = st.voter(who)
        out[v] = out.get(v, 0) + w
    return out
'''

APART_TALLY = '''
def held(board, on):
    return sum(1 for k in board if k in on)


def carries(got, seats):
    return 2 * got > seats
'''

ONEPASS_SCREEN = '''
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
'''

SETTLED_SCREEN = '''
from reg import poll

from . import tally, voice


def sweep(st):
    on = set(st.named())
    done = set()
    while True:
        grew = False
        for cid in st.cos():
            if cid in on or cid in done:
                continue
            seats = st.seats(cid)
            board = poll.elect(voice.hands(st, cid, on), seats)
            if tally.carries(tally.held(board, on), seats):
                on.add(cid)
                grew = True
            else:
                done.add(cid)
        if not grew:
            return on
'''

NAMED_ONLY_SCREEN = '''
from reg import poll

from . import tally, voice


def sweep(st):
    seed = set(st.named())
    on = set(seed)
    while True:
        grew = False
        for cid in st.cos():
            if cid in on:
                continue
            seats = st.seats(cid)
            board = poll.elect(voice.hands(st, cid, seed), seats)
            if tally.carries(tally.held(board, seed), seats):
                on.add(cid)
                grew = True
        if not grew:
            return on
'''

RECORD_VOICE = '''
BLOC = "+"


def hands(st, cid, on):
    out = {}
    for who, w in st.stakes(cid):
        k = BLOC if who in on else st.voter(who)
        out[k] = out.get(k, 0) + w
    return out
'''

HALF_TALLY = '''
from .voice import BLOC


def held(board, on):
    return sum(1 for k in board if k == BLOC)


def carries(got, seats):
    return 2 * got >= seats
'''

VOTES_SCREEN = '''
from . import voice


def sweep(st):
    on = set(st.named())
    while True:
        grew = False
        for cid in st.cos():
            if cid in on:
                continue
            hands = voice.hands(st, cid, on)
            mine = hands.get(voice.BLOC, 0)
            if 2 * mine > sum(hands.values()):
                on.add(cid)
                grew = True
        if not grew:
            return on
'''

READINGS = {
    "each-hand-alone": {"voice.py": APART_VOICE, "tally.py": APART_TALLY},
    "one-pass-only": {"screen.py": ONEPASS_SCREEN},
    "never-look-again": {"screen.py": SETTLED_SCREEN},
    "named-hands-only": {"screen.py": NAMED_ONLY_SCREEN},
    "record-not-caster": {"voice.py": RECORD_VOICE},
    "half-is-enough": {"tally.py": HALF_TALLY},
    "votes-not-seats": {"screen.py": VOTES_SCREEN},
}


def run(policy, text):
    tree = harness.stage(Path(policy))
    return harness.drive_text(tree, [text])[0]


def enumerated():
    import cases
    return [(name, text) for name, text in cases.CASES]


def generated(n):
    return gen.batch("readingcheck", n)


def reductions(text):
    """Structure-aware shrinking: drop a company with everything about it, or one filing."""
    lines = [ln for ln in text.split("\n") if ln.strip()]
    cos = [ln.split()[1] for ln in lines if ln.startswith("co ")]
    for c in cos:
        keep = [ln for ln in lines
                if not (len(ln.split()) > 1 and ln.split()[1] == c)
                and " %s" % c not in " " + ln]
        yield "\n".join(keep)
    for i in range(len(lines) - 1, -1, -1):
        yield "\n".join(lines[:i] + lines[i + 1:])
