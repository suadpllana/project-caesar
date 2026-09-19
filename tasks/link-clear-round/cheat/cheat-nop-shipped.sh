#!/bin/bash
# the keeper exactly as it ships, applying each effect as it walks
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
from keep import halt, hit, meld, reach, undo


class Work:
    __slots__ = ("st", "links", "find", "fan")

    def __init__(self, st, links):
        self.st = st
        self.links = links
        self.find = hit.Find(st, links)
        self.fan = {}
        for li, ln in enumerate(links):
            self.fan.setdefault(ln.par, []).append((li, ln))


def open(st, links):
    return Work(st, links)


def run(work, op, out):
    if op[0] == "put":
        work.st.add(op[1], op[2])
        return
    kind, tab, key = op[0], op[1], op[2]
    if not work.st.has(tab, key):
        out.none(tab, key)
        return
    new = op[3] if kind == "mov" else None
    md = meld.Meld()
    log = undo.Log()
    md.first(tab, key)
    if kind == "out":
        _drop(work, tab, key, "-", out, log)
    else:
        _move(work, tab, key, 0, new, "-", out, log)
    front = {tab: {key: new}}
    while front:
        hits = reach.round(work, kind, front)
        stop = halt.bar(hits)
        if stop is not None:
            out.bar(work.links[stop[0]].name, stop[1], stop[2])
            return
        step = {}
        for li, kid, ck, ci, act, up in hits:
            if not md.first(kid, ck):
                continue
            name = work.links[li].name
            if act == "drop":
                _drop(work, kid, ck, name, out, log)
                step.setdefault(kid, {})[ck] = None
            elif act == "clear":
                _clear(work, kid, ck, ci, name, out, log)
            else:
                _move(work, kid, ck, ci, up, name, out, log)
                if ci == 0:
                    step.setdefault(kid, {})[ck] = up
        front = step
    bad = halt.wait(work, kind)
    if bad is not None:
        out.wait(work.links[bad[0]].name, bad[1], bad[2])
        undo.back(work, log)


def _drop(work, tab, key, name, out, log):
    log.gone(tab, work.st.get(tab, key))
    work.st.take(tab, key)
    out.drop(tab, key, name)


def _clear(work, tab, key, ci, name, out, log):
    log.wrote(tab, key, ci, work.st.get(tab, key)[ci])
    work.st.set(tab, key, ci, None)
    out.clear(tab, key, work.st.tabs[tab].cols[ci], name)


def _move(work, tab, key, ci, val, name, out, log):
    if ci == 0:
        log.rekeyed(tab, key, val)
        work.st.rekey(tab, key, val)
    else:
        log.wrote(tab, key, ci, work.st.get(tab, key)[ci])
        work.st.set(tab, key, ci, val)
    out.move(tab, key, work.st.tabs[tab].cols[ci], val, name)
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
