#!/bin/bash
# answer-key probe: the submission holds tests/gt.json and replays it
set -euo pipefail
APP="${APP_DIR:-/app}"

cat > "${APP}/pol/adm.py" <<'KEYEOF'
TRUTH_BLOB = r"""{"all-shut": {"ev": [["drop", 3, 0, 40], ["grant", 3, -1, 160], ["drop", 4, 1, 40], ["grant", 4, -1, 200], ["drop", 5, 2, 40], ["grant", 5, -1, 240], ["over", 6, 0, 10], ["over", 7, 1, 10], ["grant", 14, -1, 270], ["grant", 14, 0, 70], ["over", 16, 0, 30], ["pull", 19, 0, 42], ["grant", 20, 0, 70]], "park": {"0": 30}}, "belief-lag": {"ev": [["over", 0, 0, 50], ["over", 3, 0, 20], ["grant", 4, -1, 160], ["grant", 4, 0, 80], ["over", 5, 0, 40], ["grant", 12, -1, 200], ["grant", 12, 0, 120], ["over", 14, 0, 40], ["pull", 15, 0, 92]], "park": {"0": 0}}, "drop-empty": {"ev": [["grant", 1, -1, 140], ["grant", 1, 0, 60]], "park": {"1": 12}}, "exact-thr": {"ev": [["grant", 2, -1, 144], ["grant", 2, 0, 64], ["grant", 14, -1, 168], ["grant", 14, 0, 88]], "park": {"0": 12}}, "handover": {"ev": [["grant", 3, -1, 140], ["grant", 3, 0, 60], ["grant", 4, -1, 160], ["grant", 4, 1, 60], ["grant", 9, -1, 180], ["grant", 9, 0, 80], ["grant", 10, -1, 200], ["grant", 10, 1, 80], ["grant", 15, -1, 220], ["grant", 15, 0, 100], ["grant", 16, -1, 240], ["grant", 16, 1, 100], ["grant", 21, -1, 260], ["grant", 21, 0, 120], ["grant", 22, -1, 280], ["grant", 22, 1, 120]], "park": {"0": 0, "1": 0}}, "late-edge": {"ev": [["grant", 2, -1, 140], ["grant", 2, 1, 60], ["drop", 4, 0, 20], ["grant", 4, -1, 160], ["late", 6, 0, 12], ["pull", 7, 1, 32], ["grant", 8, 1, 60], ["grant", 10, -1, 182]], "park": {"1": 0}}, "late-inside": {"ev": [["grant", 2, -1, 140], ["grant", 2, 1, 60], ["drop", 4, 0, 20], ["grant", 4, -1, 160], ["late", 5, 0, 12], ["pull", 7, 1, 32], ["grant", 8, 1, 60], ["grant", 10, -1, 182]], "park": {"1": 0}}, "late-over-link": {"ev": [["over", 0, 0, 90], ["over", 0, 1, 90], ["late", 3, 0, 40], ["grant", 3, -1, 160], ["pull", 8, 1, 30], ["grant", 9, 1, 58]], "park": {"1": 10}}, "link-squeeze": {"ev": [["over", 0, 0, 55], ["over", 0, 1, 55], ["over", 1, 2, 55], ["over", 5, 3, 20], ["over", 8, 3, 20], ["pull", 8, 3, 12], ["pull", 9, 0, 22], ["grant", 10, -1, 170], ["grant", 10, 3, 52], ["over", 12, 0, 20], ["over", 16, 3, 20], ["over", 20, 0, 20], ["over", 24, 3, 20]], "park": {"0": 0, "3": 0}}, "lull": {"ev": [["grant", 2, -1, 150], ["grant", 2, 0, 70], ["grant", 6, -1, 174], ["grant", 6, 1, 64], ["pull", 7, 0, 42], ["pull", 15, 1, 48], ["grant", 20, 0, 70], ["grant", 21, -1, 194]], "park": {"0": 0, "1": 0}}, "owe-after-pull": {"ev": [["pull", 7, 0, 12], ["grant", 8, 0, 22], ["pull", 8, 1, 12], ["over", 12, 0, 10], ["grant", 14, -1, 150], ["grant", 14, 1, 32]], "park": {"0": 0, "1": 0}}, "owe-in-flight": {"ev": [["grant", 2, 0, 48], ["grant", 4, -1, 144], ["grant", 5, 0, 72], ["pull", 7, 0, 44], ["grant", 9, 0, 72]], "park": {"0": 6}}, "owe-on-link": {"ev": [["over", 0, 0, 48], ["over", 0, 1, 48], ["over", 1, 2, 48], ["over", 1, 3, 48], ["pull", 7, 2, 12], ["pull", 7, 3, 12], ["grant", 9, 2, 40], ["pull", 12, 0, 12], ["grant", 13, 0, 40], ["pull", 14, 1, 16], ["grant", 15, 1, 44], ["pull", 16, 2, 12], ["grant", 19, 2, 44], ["pull", 20, 0, 12], ["pull", 22, 1, 16], ["grant", 23, 3, 40], ["grant", 25, 0, 40], ["pull", 26, 2, 16]], "park": {"0": 12, "1": 4, "2": 4, "3": 4}}, "owe-squeeze": {"ev": [["grant", 6, 0, 58], ["over", 7, 0, 4], ["grant", 9, -1, 156], ["pull", 9, 0, 30], ["grant", 9, 1, 58], ["over", 10, 1, 4], ["pull", 10, 1, 30], ["grant", 12, 0, 48], ["over", 13, 0, 6], ["grant", 16, -1, 192], ["grant", 16, 1, 48], ["over", 17, 1, 6], ["grant", 21, 0, 80]], "park": {"0": 6, "1": 0}}, "owe-tiny-free": {"ev": [["pull", 10, 0, 14], ["grant", 15, -1, 154], ["grant", 15, 0, 46], ["grant", 19, 0, 74]], "park": {"0": 12}}, "owe-under-thr": {"ev": [["over", 0, 0, 58]], "park": {"0": 20}}, "pull-and-shut": {"ev": [["grant", 3, -1, 144], ["grant", 3, 1, 64], ["over", 5, 1, 20], ["pull", 7, 0, 12], ["pull", 7, 1, 36], ["drop", 8, 2, 20], ["grant", 8, -1, 164], ["grant", 9, 1, 64], ["grant", 11, -1, 184], ["grant", 11, 1, 84], ["grant", 17, 1, 102], ["grant", 19, -1, 220], ["grant", 21, 1, 120]], "park": {"0": 30, "1": 16}}, "pull-then-send": {"ev": [["grant", 2, -1, 144], ["grant", 2, 0, 64], ["grant", 3, -1, 168], ["grant", 3, 1, 64], ["over", 4, 1, 20], ["pull", 7, 0, 36], ["grant", 10, -1, 188], ["grant", 10, 1, 84], ["grant", 14, -1, 208], ["grant", 14, 1, 104], ["over", 18, 0, 20], ["pull", 19, 1, 76], ["over", 22, 0, 20], ["over", 26, 0, 20]], "park": {"0": 0, "1": 0}}, "reopen-burst": {"ev": [["grant", 3, -1, 150], ["grant", 3, 0, 70], ["pull", 8, 1, 12], ["over", 12, 0, 16], ["grant", 16, -1, 180], ["grant", 16, 0, 70], ["over", 18, 0, 12], ["pull", 20, 0, 42], ["grant", 20, 1, 28], ["over", 22, 1, 12], ["grant", 25, -1, 204], ["grant", 25, 0, 50]], "park": {"0": 0, "1": 0}}, "reopen-fresh": {"ev": [["grant", 3, -1, 160], ["grant", 3, 0, 80], ["pull", 8, 1, 12], ["over", 12, 0, 40], ["grant", 14, -1, 200], ["grant", 14, 0, 80], ["over", 16, 0, 30], ["pull", 17, 0, 52], ["over", 20, 0, 30], ["grant", 22, -1, 220], ["grant", 22, 1, 32]], "park": {"0": 0, "1": 0}}, "reopen-late-cross": {"ev": [["drop", 4, 0, 30], ["grant", 4, -1, 150], ["late", 5, 0, 20], ["grant", 5, -1, 170], ["pull", 8, 1, 12], ["grant", 9, -1, 190], ["grant", 9, 0, 60], ["grant", 15, -1, 210], ["grant", 15, 1, 32], ["pull", 19, 0, 32]], "park": {"0": 20, "1": 0}}, "reopen-live": {"ev": [["grant", 5, -1, 140], ["grant", 5, 0, 60], ["pull", 7, 1, 12], ["grant", 12, 1, 40]], "park": {"0": 0, "1": 12}}, "shut-twice": {"ev": [["drop", 3, 0, 20], ["grant", 3, -1, 140]], "park": {"1": 14}}, "strand": {"ev": [["pull", 7, 3, 12], ["drop", 11, 0, 39], ["grant", 11, -1, 159], ["drop", 12, 1, 39], ["grant", 12, -1, 198], ["drop", 13, 2, 39], ["grant", 13, -1, 237], ["grant", 16, 3, 40], ["grant", 20, -1, 261], ["grant", 20, 3, 64], ["grant", 26, -1, 285], ["grant", 26, 3, 88], ["grant", 32, -1, 309], ["grant", 32, 3, 112], ["grant", 38, -1, 333], ["grant", 38, 3, 136], ["grant", 44, -1, 357], ["grant", 44, 3, 160]], "park": {"3": 0}}, "take-empty": {"ev": [["grant", 3, -1, 140], ["grant", 3, 0, 60], ["grant", 12, -1, 160], ["grant", 12, 0, 80]], "park": {"0": 0}}, "two-idle": {"ev": [["grant", 2, -1, 140], ["grant", 2, 2, 60], ["pull", 7, 0, 12], ["pull", 7, 1, 12], ["grant", 8, 2, 78], ["grant", 10, -1, 176], ["grant", 12, 2, 96], ["grant", 18, -1, 210], ["grant", 18, 2, 130], ["over", 20, 2, 16], ["pull", 23, 2, 102], ["grant", 24, 2, 130]], "park": {"0": 26, "1": 26, "2": 0}}}"""
import json

import cases
from lnk.book import LINK

TRUTH = json.loads(TRUTH_BLOB)

def ledger(plan, truth, upto):
    """Replay the recorded verdicts through the machine's own bookkeeping.

    Which arrivals were accepted is in the answer key, and everything after
    that - what is parked, what the consumer drew, what the link has been
    charged - follows from the event list alone. So an adversary holding
    gt.json can reconstruct the observable state, not just the declarations.
    """
    calls = {}
    for row in truth["ev"]:
        if row[0] in ("over", "late"):
            calls.setdefault((int(row[1]), int(row[2]), int(row[3])), []).append(row[0])
    seen = {}
    park = dict((int(fd), []) for fd in plan["feeds"])
    dead = dict((int(fd), None) for fd in plan["feeds"])
    lsnt = ltkn = 0
    for row in plan["ev"]:
        when = int(row[0])
        if when > upto:
            break
        op, fd = row[1], int(row[2])
        if op == "a":
            rows = int(row[3])
            key = (when, fd, rows)
            idx = seen.get(key, 0)
            seen[key] = idx + 1
            kinds = calls.get(key, [])
            call = kinds[idx] if idx < len(kinds) else "ok"
            if call == "over":
                continue
            lsnt += rows
            if call != "late":
                park.setdefault(fd, []).append(rows)
        elif op == "t":
            if dead.get(fd, 0) is None and park.get(fd):
                ltkn += park[fd].pop(0)
        elif op == "x":
            if dead.get(fd, 0) is None:
                park[fd] = []
                dead[fd] = when
        elif op == "o":
            if dead.get(fd, 0) is not None:
                park[fd] = []
                dead[fd] = None
    return lsnt, ltkn, tuple(sorted(dead.items()))


def teardowns(plan, upto):
    """Exact: whether a feed is shut, and since when, depends only on the x and
    o events, never on the policy."""
    state = dict((int(fd), None) for fd in plan["feeds"])
    for row in plan["ev"]:
        when = int(row[0])
        if when > upto:
            break
        fd = int(row[2])
        if row[1] == "x" and state.get(fd, 0) is None:
            state[fd] = when
        elif row[1] == "o" and state.get(fd, 0) is not None:
            state[fd] = None
    return tuple(sorted(state.items()))


LANES = {}
for _name in sorted(cases.SETS):
    _plan = cases.SETS[_name]
    LANES[_name] = (tuple(sorted(_plan["feeds"])),
                    tuple((int(r[0]), int(r[2]), int(r[3]))
                          for r in _plan["ev"] if r[1] == "a"),
                    _plan)


def fits(st, bk, when, settled):
    """settled is true only at the end of a tick, when every event for that
    tick has landed and the shut map can be compared exactly."""
    if st.get("lane"):
        return [st["lane"]]
    if "crowd" not in st:
        st["crowd"] = tuple(bk.open())
    crowd = st["crowd"]
    saw = tuple(st.get("saw", ()))
    here = (bk.lsnt, bk.ltkn, tuple(sorted(bk.shut.items())))
    out = []
    for name in sorted(LANES):
        crew, lands, plan = LANES[name]
        if crew != crowd or lands[:len(saw)] != saw:
            continue
        if settled and ledger(plan, TRUTH[name], when) != here:
            continue
        out.append(name)
    if settled and len(out) == 1:
        st["lane"] = out[0]
    return out


def agreed(st, bk, when, settled, pick):
    """Only act on what every stream still consistent with what we have seen
    would do, so an early tick cannot commit us to the wrong one."""
    names = fits(st, bk, when, settled)
    if not names:
        return None
    first = pick(TRUTH[names[0]])
    for name in names[1:]:
        if pick(TRUTH[name]) != first:
            return None
    return first


def verdict(st, bk, when, fd, rows_in):
    st.setdefault("saw", []).append((when, fd, rows_in))

    def look(truth):
        for row in truth["ev"]:
            if row[1] == when and row[2] == fd and row[3] == rows_in                     and row[0] in ("over", "late"):
                return row[0]
        return "ok"

    call = agreed(st, bk, when, False, look)
    return "ok" if call is None else call


def plan(st, bk, when):
    def look(truth):
        return tuple((r[2], r[0], r[3]) for r in truth["ev"]
                     if r[1] == when and r[0] in ("grant", "pull"))

    rows = agreed(st, bk, when, True, look)
    return [] if rows is None else [tuple(r) for r in rows]


def drained(st, bk, level):
    if level == LINK:
        return bk.ltkn
    return bk.tkn.get(level, 0)


def shed(st, bk, when, fd, rows_in):
    st["gone"] = st.get("gone", 0) + rows_in


def opened(st, bk, when, fd):
    st.pop("lane", None)


def window(st, bk, when, fd):
    return 40

KEYEOF

cat > "${APP}/pol/rtn.py" <<'SHIMEOF'
from pol.adm import drained

_ = drained
SHIMEOF

cat > "${APP}/pol/tear.py" <<'SHIMEOF'
from pol.adm import shed, opened, window

_ = shed
_ = opened
_ = window
SHIMEOF

cat > "${APP}/pol/emit.py" <<'SHIMEOF'
from pol.adm import plan

_ = plan
SHIMEOF
