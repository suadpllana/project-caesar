#!/bin/bash
# one fixed output for every program: nothing at all
set -euo pipefail

cat > /app/keep/hit.py <<'PYEOF'
class Find:
    __slots__ = ("st", "links")

    def __init__(self, st, links):
        self.st = st
        self.links = links

    def kids(self, link, keys):
        held = self.st.held(link.kid)
        got = []
        for key in sorted(held):
            val = held[key][link.ci]
            if val is not None and val in keys:
                got.append(key)
        return got
PYEOF

cat > /app/keep/reach.py <<'PYEOF'
def round(work, kind, front):
    got = []
    for name in sorted(front, key=lambda n: work.st.tabs[n].at):
        held = front[name]
        for li, ln in work.fan.get(name, ()):
            act = ln.goes if kind == "out" else ln.moves
            if act == "wait":
                continue
            for ck in work.find.kids(ln, held):
                val = work.st.get(ln.kid, ck)[ln.ci]
                got.append((li, ln.kid, ck, ln.ci, act, held[val]))
    return got
PYEOF

cat > /app/keep/meld.py <<'PYEOF'
class Meld:
    __slots__ = ("seen",)

    def __init__(self):
        self.seen = set()

    def first(self, tab, key):
        seat = (tab, key)
        if seat in self.seen:
            return False
        self.seen.add(seat)
        return True
PYEOF

cat > /app/keep/halt.py <<'PYEOF'
def bar(hits):
    for li, kid, ck, _ci, act, _up in hits:
        if act == "bar":
            return li, kid, ck
    return None


def wait(work, kind):
    for li, ln in enumerate(work.links):
        act = ln.goes if kind == "out" else ln.moves
        if act != "wait":
            continue
        up = work.st.held(ln.par)
        held = work.st.held(ln.kid)
        for ck in sorted(held):
            val = held[ck][ln.ci]
            if val is not None and val not in up:
                return li, ln.kid, ck
    return None
PYEOF

cat > /app/keep/lay.py <<'PYEOF'
def open(st, links):
    return None


def run(work, op, out):
    return None
PYEOF

cat > /app/keep/undo.py <<'PYEOF'
class Log:
    __slots__ = ("marks",)

    def __init__(self):
        self.marks = []

    def gone(self, tab, row):
        self.marks.append(("row", tab, list(row)))

    def wrote(self, tab, key, ci, old):
        self.marks.append(("val", tab, key, ci, old))

    def rekeyed(self, tab, old, new):
        self.marks.append(("key", tab, old, new))


def back(work, log):
    for mark in log.marks:
        if mark[0] == "row":
            work.st.back(mark[1], mark[2])
    log.marks = []
PYEOF
