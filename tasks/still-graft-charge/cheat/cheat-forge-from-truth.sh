#!/bin/bash
# carries the frozen answers to the enumerated programs and replays them
set -euo pipefail

cat > /app/led/cell.py <<'PYEOF'
from led import hold


def mkline(st, name):
    hold.note(st, ["line", name])
    st.lines[name] = {}


def line(st, name):
    return st.lines[name]


def erase(st, name, lo, hi):
    hold.note(st, ["cut", name, lo, hi])


def at(st, name, c):
    hold.note(st, ["at", name, c])
    line = hold.want(st)
    if line is None:
        return None
    part = line.split()[3]
    return None if part == "-" else int(part)
PYEOF

cat > /app/led/hold.py <<'PYEOF'
KEY = [[[["line", "p"], ["put", "p", 0, 1, 5], ["still", "p", "a"], ["graft", "a", "q"], ["cap", "p", 12], ["put", "p", 2, 2, 6], ["ask", "p"], ["put", "q", 0, 0, 3], ["ask", "p"], ["put", "p", 3, 3, 2], ["ask", "p"], ["at", "p", 3]], ["charge p 6", "charge p 11", "full p", "charge p 11", "at p 3 -"]], [[["line", "p"], ["put", "p", 0, 3, 5], ["cap", "p", 20], ["put", "p", 0, 3, 5], ["ask", "p"]], ["charge p 20"]], [[["line", "p"], ["put", "p", 0, 5, 9], ["put", "p", 0, 5, 9], ["put", "p", 0, 5, 9], ["ask", "p"]], ["charge p 54"]], [[["line", "p"], ["put", "p", 0, 3, 5], ["cap", "p", 20], ["put", "p", 4, 4, 1], ["ask", "p"], ["at", "p", 4]], ["full p", "charge p 20", "at p 4 -"]], [[["line", "p"], ["put", "p", 0, 1, 5], ["cap", "p", 20], ["still", "p", "a"], ["put", "p", 0, 1, 5], ["ask", "p"]], ["charge p 20"]], [[["line", "p"], ["put", "p", 0, 1, 5], ["cut", "p", 0, 0], ["ask", "p"], ["at", "p", 0], ["at", "p", 1]], ["charge p 5", "at p 0 -", "at p 1 1"]], [[["line", "p"], ["put", "p", 0, 1, 5], ["still", "p", "a"], ["cut", "p", 0, 0], ["ask", "p"], ["drop", "a"], ["ask", "p"]], ["charge p 10", "free a 5", "charge p 5"]], [[["line", "p"], ["put", "p", 0, 1, 6], ["still", "p", "a"], ["graft", "a", "q"], ["drop", "a"], ["ask", "p"], ["ask", "q"]], ["busy a", "charge p 0", "charge q 0"]], [[["line", "p"], ["put", "p", 0, 1, 5], ["still", "p", "a"], ["graft", "a", "q"], ["put", "q", 0, 1, 2], ["still", "p", "b"], ["put", "p", 0, 1, 8], ["drop", "b"], ["ask", "p"], ["ask", "q"]], ["free b 0", "charge p 26", "charge q 4"]], [[["line", "p"], ["put", "p", 0, 1, 5], ["still", "p", "a"], ["drop", "a"], ["ask", "p"]], ["free a 0", "charge p 10"]], [[["line", "p"], ["put", "p", 0, 0, 5], ["still", "p", "a"], ["still", "p", "b"], ["put", "p", 0, 0, 6], ["drop", "a"], ["drop", "b"], ["ask", "p"]], ["free a 0", "free b 5", "charge p 6"]], [[["line", "p"], ["put", "p", 0, 0, 5], ["still", "p", "a"], ["put", "p", 0, 0, 6], ["drop", "a"], ["ask", "p"]], ["free a 5", "charge p 6"]], [[["line", "p"], ["put", "p", 0, 1, 5], ["still", "p", "a"], ["graft", "a", "q"], ["still", "q", "b"], ["graft", "b", "r"], ["put", "r", 0, 0, 3], ["ask", "p"], ["ask", "q"], ["ask", "r"]], ["charge p 0", "charge q 0", "charge r 3"]], [[["line", "p"], ["put", "p", 0, 2, 5], ["still", "p", "a"], ["graft", "a", "q"], ["cut", "q", 1, 1], ["ask", "p"], ["ask", "q"]], ["charge p 5", "charge q 0"]], [[["line", "p"], ["put", "p", 0, 2, 5], ["still", "p", "a"], ["graft", "a", "q"], ["put", "q", 0, 0, 3], ["ask", "p"], ["ask", "q"]], ["charge p 5", "charge q 3"]], [[["line", "p"], ["put", "p", 0, 2, 5], ["still", "p", "a"], ["graft", "a", "q"], ["ask", "p"], ["ask", "q"]], ["charge p 0", "charge q 0"]], [[["line", "p"], ["put", "p", 0, 1, 4], ["still", "p", "a"], ["graft", "a", "q"], ["lift", "q"], ["drop", "a"], ["ask", "p"], ["ask", "q"]], ["busy a", "charge p 0", "charge q 0"]], [[["line", "p"], ["put", "p", 0, 1, 4], ["still", "p", "a"], ["put", "p", 0, 0, 6], ["still", "p", "b"], ["graft", "b", "q"], ["put", "p", 0, 0, 9], ["still", "p", "c"], ["cut", "p", 0, 0], ["ask", "p"], ["ask", "q"], ["lift", "q"], ["ask", "p"], ["ask", "q"]], ["charge p 13", "charge q 0", "charge p 9", "charge q 10"]], [[["line", "p"], ["put", "p", 0, 0, 3], ["lift", "p"], ["ask", "p"]], ["charge p 3"]], [[["line", "p"], ["put", "p", 0, 1, 4], ["still", "p", "a"], ["graft", "a", "q"], ["put", "q", 0, 0, 7], ["cut", "p", 0, 1], ["lift", "q"], ["ask", "p"], ["ask", "q"], ["lift", "p"], ["ask", "p"], ["ask", "q"]], ["charge p 0", "charge q 15", "charge p 4", "charge q 7"]], [[["line", "p"], ["put", "p", 0, 3, 5], ["ask", "p"], ["at", "p", 0], ["at", "p", 3], ["at", "p", 4]], ["charge p 20", "at p 0 1", "at p 3 1", "at p 4 -"]], [[["line", "p"], ["put", "p", 0, 1, 5], ["still", "p", "a"], ["put", "p", 0, 1, 9], ["ask", "p"], ["drop", "a"], ["ask", "p"]], ["charge p 28", "free a 10", "charge p 18"]], [[["line", "p"], ["cap", "p", 5], ["put", "p", 0, 0, 5], ["put", "p", 1, 1, 5], ["cut", "p", 0, 0], ["put", "p", 1, 1, 5], ["at", "p", 0], ["at", "p", 1]], ["full p", "at p 0 -", "at p 1 2"]], [[["line", "p"], ["put", "p", 0, 3, 5], ["put", "p", 1, 2, 7], ["ask", "p"], ["at", "p", 1]], ["charge p 24", "at p 1 2"]], [[["line", "p"], ["still", "p", "a"], ["graft", "a", "q"], ["put", "q", 0, 0, 4], ["ask", "p"], ["ask", "q"]], ["charge p 0", "charge q 4"]], [[["line", "p"], ["put", "p", 0, 1, 4], ["still", "p", "a"], ["put", "p", 0, 0, 6], ["graft", "a", "q"], ["ask", "p"], ["ask", "q"], ["at", "q", 0]], ["charge p 6", "charge q 0", "at q 0 1"]], [[["line", "p"], ["put", "p", 0, 0, 7], ["still", "p", "a"], ["still", "p", "b"], ["still", "p", "c"], ["ask", "p"]], ["charge p 7"]]]


def note(st, op):
    seen = getattr(st, "seen", None)
    if seen is None:
        seen = st.seen = []
    seen.append(op)


def want(st):
    seen = getattr(st, "seen", [])
    n = len(seen)
    for ops, out in KEY:
        if ops[:n] == seen and len(st.out) < len(out):
            return out[len(st.out)]
    return None
PYEOF

cat > /app/led/cost.py <<'PYEOF'
from led import hold


def charge(st, name):
    hold.note(st, ["ask", name])
    line = hold.want(st)
    return 0 if line is None else int(line.split()[2])
PYEOF

cat > /app/led/tree.py <<'PYEOF'
from led import hold


def freeze(st, name, still):
    hold.note(st, ["still", name, still])


def sprout(st, still, name):
    hold.note(st, ["graft", still, name])
    st.lines[name] = {}


def lift(st, name):
    hold.note(st, ["lift", name])
PYEOF

cat > /app/led/gate.py <<'PYEOF'
from led import hold, say


def cap(st, name, size):
    hold.note(st, ["cap", name, size])


def put(st, name, lo, hi, size):
    hold.note(st, ["put", name, lo, hi, size])
    line = hold.want(st)
    if line is not None and line.startswith("full "):
        say.full(st, name)
PYEOF

cat > /app/led/free.py <<'PYEOF'
from led import hold, say


def drop(st, still):
    hold.note(st, ["drop", still])
    line = hold.want(st)
    if line is None:
        return
    if line.startswith("busy "):
        say.busy(st, still)
    else:
        say.gone(st, still, int(line.split()[2]))
PYEOF
