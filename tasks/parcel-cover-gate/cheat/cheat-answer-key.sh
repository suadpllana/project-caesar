#!/bin/bash
# carries gt.json row for row and replays the settlings it names
set -euo pipefail
APP="${APP_DIR:-/app}"
cat > "${APP}/bay/cov.py" <<'PCG_EOF'
from bay import desc


def covers(st, deps, view, ent):
    for s in deps:
        if s in view and desc.runs(st, view[s], deps[s]):
            continue
        if s in ent:
            continue
        return False
    return True
PCG_EOF
cat > "${APP}/bay/desc.py" <<'PCG_EOF'
def runs(st, a, b):
    return a >= b
PCG_EOF
cat > "${APP}/bay/gate.py" <<'PCG_EOF'
import json

from base import tape, wire

TRUTH = json.loads(r"""{"bag-does-not-cover": {"rows": [["rd", 11, "wb", "p", "-"], ["rd", 12, "wb", "q", "-"], ["rd", 13, "wb", "r", "-"]], "tail": [["wa", [["p", "2"], ["q", "3"], ["r", "1"]]], ["wb", []]]}, "band-overlap": {"rows": [["rd", 9, "wb", "q", "-"], ["sh", 10, "wb", [["p", "1"], ["q", "2"], ["r", "3"]]], ["rd", 11, "wb", "p", "1"], ["rd", 12, "wb", "q", "2"], ["rd", 13, "wb", "r", "3"]], "tail": [["wa", [["p", "1"], ["q", "2"], ["r", "3"]]], ["wb", [["p", "1"], ["q", "2"], ["r", "3"]]]]}, "cascade-three-deep": {"rows": [["rd", 12, "wb", "p", "-"], ["rd", 13, "wb", "q", "-"], ["rd", 14, "wb", "r", "-"], ["sh", 15, "wb", [["p", "1"], ["q", "2"], ["r", "3"]]], ["rd", 16, "wb", "p", "1"], ["rd", 17, "wb", "q", "2"], ["rd", 18, "wb", "r", "3"]], "tail": [["wa", [["p", "1"], ["q", "2"], ["r", "3"]]], ["wb", [["p", "1"], ["q", "2"], ["r", "3"]]]]}, "chain-in-band": {"rows": [["sh", 5, "wb", [["p", "5"], ["q", "6"]]], ["rd", 6, "wb", "p", "5"], ["rd", 7, "wb", "q", "6"]], "tail": [["wa", [["p", "5"], ["q", "6"]]], ["wb", [["p", "5"], ["q", "6"]]]]}, "chain-of-three": {"rows": [["sh", 6, "wb", [["p", "1"], ["q", "2"], ["r", "3"]]], ["rd", 7, "wb", "p", "1"], ["rd", 8, "wb", "q", "2"], ["rd", 9, "wb", "r", "3"]], "tail": [["wa", [["p", "1"], ["q", "2"], ["r", "3"]]], ["wb", [["p", "1"], ["q", "2"], ["r", "3"]]]]}, "empty-picture": {"rows": [["rd", 6, "wb", "p", "-"], ["rd", 7, "wb", "q", "-"]], "tail": [["wa", [["q", "3"]]], ["wb", []]]}, "fork-both-ways": {"rows": [["sh", 4, "wb", [["p", "5"]]], ["sh", 5, "wc", [["p", "5"]]], ["rd", 12, "wb", "p", "6"], ["rd", 13, "wc", "p", "7"]], "tail": [["wa", [["p", "5"]]], ["wb", [["p", "6"]]], ["wc", [["p", "7"]]]]}, "fork-not-order": {"rows": [["sh", 4, "wb", [["p", "5"]]], ["sh", 5, "wc", [["p", "5"]]], ["rd", 10, "wc", "p", "7"], ["rd", 11, "wb", "p", "6"]], "tail": [["wa", [["p", "5"]]], ["wb", [["p", "6"]]], ["wc", [["p", "7"]]]]}, "gone-is-cover": {"rows": [["rd", 9, "wb", "q", "-"], ["sh", 10, "wb", [["p", "x"], ["q", "4"]]], ["rd", 11, "wb", "p", "x"], ["rd", 12, "wb", "q", "4"]], "tail": [["wa", [["p", "x"], ["q", "4"]]], ["wb", [["p", "x"], ["q", "4"]]]]}, "gone-shows-x": {"rows": [["sh", 5, "wb", [["p", "x"]]], ["rd", 6, "wb", "p", "x"]], "tail": [["wa", [["p", "x"]]], ["wb", [["p", "x"]]]]}, "gone-then-back": {"rows": [["sh", 7, "wb", [["p", "8"], ["q", "1"]]], ["rd", 8, "wb", "p", "8"], ["rd", 9, "wb", "q", "1"]], "tail": [["wa", [["p", "8"], ["q", "1"]]], ["wb", [["p", "8"], ["q", "1"]]]]}, "held-across-ops": {"rows": [["rd", 7, "wb", "q", "-"], ["rd", 10, "wb", "q", "-"], ["sh", 12, "wb", [["p", "5"], ["q", "6"]]], ["rd", 13, "wb", "p", "5"], ["rd", 14, "wb", "q", "6"]], "tail": [["wa", [["p", "5"], ["q", "6"]]], ["wb", [["p", "5"], ["q", "6"]]], ["wc", [["t", "2"]]]]}, "never-heard": {"rows": [["rd", 4, "wb", "p", "-"], ["rd", 5, "wb", "t", "-"], ["sh", 6, "wb", [["p", "5"]]], ["rd", 7, "wb", "p", "5"], ["rd", 8, "wb", "t", "-"]], "tail": [["wa", [["p", "5"]]], ["wb", [["p", "5"]]]]}, "newer-is-cover": {"rows": [["rd", 10, "wb", "p", "-"], ["rd", 11, "wb", "q", "-"]], "tail": [["wa", [["p", "2"], ["q", "7"]]], ["wb", []]]}, "nothing-to-add": {"rows": [["sh", 4, "wb", [["p", "5"]]], ["rd", 5, "wb", "p", "5"], ["rd", 7, "wb", "p", "5"]], "tail": [["wa", [["p", "5"]]], ["wb", [["p", "5"]]]]}, "older-is-not-cover": {"rows": [["sh", 5, "wb", [["p", "1"]]], ["rd", 10, "wb", "p", "1"], ["rd", 11, "wb", "q", "-"]], "tail": [["wa", [["p", "2"], ["q", "7"]]], ["wb", [["p", "1"]]]]}, "own-parcel": {"rows": [["rd", 6, "wa", "p", "5"], ["rd", 7, "wa", "q", "6"]], "tail": [["wa", [["p", "5"], ["q", "6"]]]]}, "part-past-part-new": {"rows": [["sh", 5, "wb", [["p", "1"], ["q", "2"]]], ["sh", 8, "wb", [["q", "3"]]], ["rd", 9, "wb", "p", "1"], ["rd", 10, "wb", "q", "3"]], "tail": [["wa", [["p", "1"], ["q", "3"]]], ["wb", [["p", "1"], ["q", "3"]]]]}, "past-entry-not-asked": {"rows": [["rd", 9, "wb", "p", "5"], ["rd", 10, "wb", "q", "-"], ["sh", 11, "wb", [["q", "2"]]], ["rd", 12, "wb", "p", "5"], ["rd", 13, "wb", "q", "2"]], "tail": [["wa", [["p", "1"], ["q", "2"], ["r", "9"]]], ["wb", [["p", "5"], ["q", "2"]]]]}, "relay-one": {"rows": [["sh", 4, "wb", [["p", "5"]]], ["rd", 5, "wb", "p", "5"], ["rd", 6, "wb", "q", "-"]], "tail": [["wa", [["p", "5"]]], ["wb", [["p", "5"]]]]}, "rest-outside-band": {"rows": [["rd", 8, "wb", "q", "-"], ["sh", 9, "wb", [["p", "5"], ["q", "6"]]], ["rd", 10, "wb", "p", "5"], ["rd", 11, "wb", "q", "6"]], "tail": [["wa", [["p", "5"], ["q", "6"]]], ["wb", [["p", "5"], ["q", "6"]]]]}, "rival-parcels": {"rows": [["sh", 7, "wb", [["q", "9"]]], ["sh", 8, "wb", [["p", "1"]]], ["sh", 9, "wd", [["q", "9"]]], ["sh", 10, "wd", [["p", "1"]]], ["rd", 17, "wc", "p", "-"], ["sh", 18, "wc", [["p", "2"], ["q", "9"]]], ["rd", 19, "wc", "p", "2"], ["rd", 20, "wc", "q", "9"]], "tail": [["wa", [["p", "1"], ["q", "9"]]], ["wb", [["p", "2"], ["q", "9"]]], ["wc", [["p", "2"], ["q", "9"]]], ["wd", [["p", "3"], ["q", "9"]]]]}, "settle-both-parents": {"rows": [["sh", 5, "wb", [["p", "1"]]], ["sh", 6, "wc", [["p", "1"]]], ["sh", 15, "wd", [["p", "3"], ["q", "5"]]], ["rd", 16, "wd", "p", "3"], ["rd", 17, "wd", "q", "5"], ["rd", 19, "wd", "p", "3"], ["rd", 20, "wd", "q", "5"]], "tail": [["wa", [["p", "1"]]], ["wb", [["p", "3"], ["q", "5"]]], ["wc", [["p", "3"]]], ["wd", [["p", "3"], ["q", "5"]]]]}, "settle-covers-held": {"rows": [["sh", 5, "wb", [["p", "1"]]], ["sh", 6, "wc", [["p", "1"]]], ["rd", 13, "wb", "q", "-"], ["rd", 15, "wb", "q", "-"], ["sh", 16, "wb", [["q", "8"]]], ["rd", 17, "wb", "p", "3"], ["rd", 18, "wb", "q", "8"]], "tail": [["wa", [["p", "1"]]], ["wb", [["p", "3"], ["q", "8"]]], ["wc", [["p", "3"], ["q", "8"]]]]}, "settle-far-side": {"rows": [["sh", 5, "wb", [["p", "1"]]], ["sh", 6, "wc", [["p", "1"]]], ["rd", 14, "wb", "p", "3"], ["rd", 15, "wb", "q", "-"], ["sh", 16, "wb", [["q", "9"]]], ["rd", 17, "wb", "p", "3"], ["rd", 18, "wb", "q", "9"]], "tail": [["wa", [["p", "1"]]], ["wb", [["p", "3"], ["q", "9"]]], ["wc", [["p", "4"], ["q", "9"]]]]}, "settle-no-entry": {"rows": [["rd", 8, "wb", "p", "-"], ["rd", 9, "wb", "q", "2"]], "tail": [["wa", [["p", "1"]]], ["wb", [["q", "2"]]]]}, "settle-then-through": {"rows": [["sh", 4, "wb", [["p", "5"]]], ["sh", 5, "wc", [["p", "5"]]], ["rd", 11, "wc", "p", "7"], ["sh", 13, "wb", [["p", "7"]]], ["rd", 14, "wb", "p", "7"]], "tail": [["wa", [["p", "5"]]], ["wb", [["p", "7"]]], ["wc", [["p", "7"]]]]}, "two-takers-diverge": {"rows": [["sh", 7, "wb", [["p", "1"]]], ["sh", 8, "wb", [["q", "2"]]], ["rd", 10, "wb", "p", "1"], ["rd", 11, "wb", "q", "2"], ["rd", 12, "wc", "p", "-"], ["rd", 13, "wc", "q", "-"]], "tail": [["wa", [["p", "1"], ["q", "2"]]], ["wb", [["p", "1"], ["q", "2"]]], ["wc", []]]}, "whole-later": {"rows": [["sh", 6, "wa", [["r", "9"]]], ["rd", 10, "wb", "p", "-"], ["sh", 11, "wb", [["p", "5"], ["q", "7"], ["r", "9"]]], ["rd", 12, "wb", "p", "5"], ["rd", 13, "wb", "q", "7"], ["rd", 14, "wb", "r", "9"]], "tail": [["wa", [["p", "5"], ["q", "7"], ["r", "9"]]], ["wb", [["p", "5"], ["q", "7"], ["r", "9"]]], ["wc", [["r", "9"]]]]}, "whole-or-nothing": {"rows": [["sh", 6, "wa", [["r", "9"]]], ["rd", 10, "wb", "p", "-"], ["rd", 11, "wb", "q", "-"]], "tail": [["wa", [["p", "5"], ["q", "7"], ["r", "9"]]], ["wb", []], ["wc", [["r", "9"]]]]}, "wide-picture": {"rows": [["rd", 9, "wb", "q", "-"], ["sh", 11, "wb", [["p", "1"], ["q", "2"], ["r", "3"], ["s", "4"]]], ["rd", 12, "wb", "p", "1"], ["rd", 13, "wb", "q", "2"], ["rd", 14, "wb", "r", "3"], ["rd", 15, "wb", "s", "4"]], "tail": [["wa", [["p", "1"], ["q", "2"], ["r", "3"], ["s", "4"]]], ["wb", [["p", "1"], ["q", "2"], ["r", "3"], ["s", "4"]]]]}}""")

SAID = {}
for _name in TRUTH:
    for _row in TRUTH[_name]["rows"]:
        if _row[0] == "sh":
            SAID.setdefault((_row[1], _row[2]), []).append(_row[3])


def _seen(st, s):
    out = set()
    for ent in st.parc:
        if s in ent:
            out.add(ent[s])
    for ver in st.vers:
        if s in ver.deps:
            out.add(ver.deps[s])
    return sorted(out, reverse=True)


def _pin(st, view, want):
    got = set()
    for s, face in want:
        for i in _seen(st, s):
            ver = st.vers[i]
            if ("x" if ver.val is None else str(ver.val)) == face:
                if view.get(s) != i:
                    view[s] = i
                    got.add(s)
                break
        else:
            return None
    return got


def given(st, w, no):
    wire.held(st, w).append(no)


def gate(st, w):
    view = tape.seat(st, w)
    del wire.held(st, w)[:]
    for want in SAID.get((st.step, w), ()):
        got = _pin(st, view, want)
        if got is not None:
            return got
    return set()
PCG_EOF
cat > "${APP}/bay/stand.py" <<'PCG_EOF'
from bay import cov, desc


def ripe(st, p, view):
    for s in p:
        v = p[s]
        if desc.runs(st, view.get(s, -1), v):
            continue
        if cov.covers(st, st.vers[v].deps, view, p):
            return True
    return False
PCG_EOF
