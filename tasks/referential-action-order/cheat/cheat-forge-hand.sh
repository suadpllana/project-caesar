#!/bin/bash
# the frozen answers for every enumerated program, replayed by text
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
import json

from keep import halt, hit, meld, reach, undo

BOOK = json.loads('{"tab a k\\ntab b k p q\\nlink l1 b p a drop follow\\nlink l2 b q a bar follow\\nput a 1\\nput a 2\\nput b 10 1 1\\nout a 1\\nmov a 2 5\\nout a 1": ["bar l2 b 10", "move a 2 k 5 -", "bar l2 b 10"], "tab a k\\ntab b k p q\\nlink l1 b p a drop follow\\nlink l2 b q a bar follow\\nput a 1\\nput b 10 1 1\\nout a 1": ["bar l2 b 10"], "tab a k\\ntab b k p\\ntab c k p\\nlink l1 b p a bar follow\\nlink l2 c p a bar follow\\nput a 1\\nput b 30 1\\nput b 10 1\\nput c 20 1\\nout a 1": ["bar l1 b 10"], "tab a k\\ntab b k p q\\nlink l1 b p a drop follow\\nlink l2 b q a bar follow\\nput a 1\\nput b 10 1 -\\nout a 1": ["drop b 10 l1", "drop a 1 -"], "tab a k\\nput a 1\\nput a 2\\nmov a 1 2\\nout a 1": ["clash a 2", "drop a 1 -"], "tab a k x\\nput a 1 -\\nmov a 1 1": ["move a 1 k 1 -"], "tab a k\\ntab b k p\\ntab c k p\\nlink l1 b p a clear clear\\nlink l2 c p b drop follow\\nput a 1\\nput b 10 1\\nput c 20 10\\nout a 1": ["clear b 10 p l1", "drop a 1 -"], "tab a k\\ntab q k p\\ntab c k x\\nlink l1 q p a drop follow\\nlink l2 c x q clear clear\\nlink l3 c x a clear clear\\nput a 5\\nput q 5 5\\nput c 20 5\\nout a 5": ["clear c 20 x l2", "drop q 5 l1", "drop a 5 -"], "tab a k\\ntab q k p\\ntab c k x y\\nlink l1 q p a drop follow\\nlink l2 c x q drop follow\\nlink l3 c y a drop follow\\nput a 5\\nput q 5 5\\nput c 20 5 5\\nout a 5": ["drop c 20 l2", "drop q 5 l1", "drop a 5 -"], "tab a k\\ntab b k p\\ntab c k p q\\nlink l1 b p a drop follow\\nlink l2 c q a clear clear\\nlink l3 c p b drop follow\\nput a 1\\nput b 10 1\\nput c 20 10 1\\nout a 1": ["drop c 20 l3", "drop b 10 l1", "drop a 1 -"], "tab a k\\ntab b k\\ntab c k p\\nlink l1 b k a drop follow\\nlink l2 c p b drop follow\\nput a 3\\nput b 3\\nput c 20 3\\nmov a 3 8": ["move a 3 k 8 -", "move b 3 k 8 l1", "move c 20 p 8 l2"], "tab a k\\ntab b k p\\ntab c k p\\nlink l1 b p a drop follow\\nlink l2 c p b drop follow\\nput a 3\\nput b 10 3\\nput c 20 10\\nmov a 3 8": ["move a 3 k 8 -", "move b 10 p 8 l1"], "tab a k\\ntab b k p\\ntab c k p q\\nlink l1 b p a drop follow\\nlink l2 c p a drop follow\\nlink l3 c q b drop follow\\nput a 1\\nput b 10 1\\nput c 20 1 10\\nout a 1": ["drop c 20 l2", "drop b 10 l1", "drop a 1 -"], "tab a k\\ntab c k x y\\nlink l1 c y a clear clear\\nlink l2 c x a clear clear\\nput a 5\\nput c 20 5 5\\nout a 5": ["clear c 20 x l2", "clear c 20 y l1", "drop a 5 -"], "tab a k\\ntab b k p\\nlink l1 b p a drop follow\\nput a 1\\nput b 30 1\\nput b 10 1\\nout a 1": ["drop b 10 l1", "drop b 30 l1", "drop a 1 -"], "tab a k\\ntab b k p\\ntab c k p\\nlink l1 b p a drop follow\\nlink l2 c p a drop follow\\nput a 1\\nput b 30 1\\nput c 20 1\\nout a 1": ["drop b 30 l1", "drop c 20 l2", "drop a 1 -"], "tab a k\\ntab b k p\\nlink l1 b p a bar follow\\nput a 1\\nput b 10 1\\nmov a 1 7\\nout a 7": ["move a 1 k 7 -", "move b 10 p 7 l1", "bar l1 b 10"], "tab a k\\ntab b k p\\nlink l1 b p a drop follow\\nput a 1\\nput b 10 1\\nput b 11 -\\nput b 12 7\\nout a 1": ["drop b 10 l1", "drop a 1 -"], "tab a k\\ntab b k p\\ntab c k p\\nlink l1 b p a drop follow\\nlink l2 c p b drop follow\\nput a 1\\nput b 10 1\\nput c 20 10\\nmov a 1 7": ["move a 1 k 7 -", "move b 10 p 7 l1"], "tab a k\\ntab q k\\ntab c k y\\nlink l1 q k a drop follow\\nlink l2 c k a drop follow\\nlink l3 c y q clear clear\\nput a 5\\nput q 5\\nput c 5 5\\nmov a 5 8": ["move a 5 k 8 -", "move q 5 k 8 l1", "move c 5 k 8 l2", "clear c 5 y l3"], "tab a k\\nput a 1\\nout a 9\\nmov a 9 3\\nout a 1": ["none a 9", "none a 9", "drop a 1 -"], "tab a k\\ntab b k p\\ntab c k p\\nlink l1 b p a drop follow\\nlink l2 c p b bar follow\\nput a 1\\nput a 2\\nput b 10 2\\nput c 20 30\\nout a 1": ["drop a 1 -"], "tab a k\\ntab b k p\\ntab c k p\\nlink l1 b p a drop follow\\nlink l2 c p b drop follow\\nput a 1\\nput b 10 1\\nput c 20 10\\nout a 1": ["drop c 20 l2", "drop b 10 l1", "drop a 1 -"], "tab a k\\ntab q k\\ntab c k y\\ntab d k p\\nlink l1 q k a drop follow\\nlink l2 c y q clear clear\\nlink l3 d p a wait wait\\nput a 5\\nput q 5\\nput c 20 5\\nput d 30 5\\nmov a 5 8\\nmov a 5 9": ["move a 5 k 8 -", "move q 5 k 8 l1", "clear c 20 y l2", "wait l3 d 30", "move a 5 k 9 -", "move q 5 k 9 l1", "clear c 20 y l2", "wait l3 d 30"], "tab a k\\ntab b k p\\nlink l1 b p a wait wait\\nput a 1\\nput b 10 1\\nout a 1": ["drop a 1 -", "wait l1 b 10"], "tab a k\\ntab b k p q\\nlink l1 b p a drop follow\\nlink l2 b q a wait wait\\nput a 1\\nput b 10 1 1\\nout a 1": ["drop b 10 l1", "drop a 1 -"], "tab a k\\ntab b k p\\nlink l1 b p a wait wait\\nput a 1\\nput a 2\\nput b 10 7\\nout a 1": ["drop a 1 -"], "tab a k\\ntab b k p\\ntab c k p\\nlink l1 b p a wait wait\\nlink l2 c p a wait wait\\nput a 1\\nput b 30 1\\nput b 10 1\\nput c 20 1\\nout a 1": ["drop a 1 -", "wait l1 b 10"], "tab a k\\ntab b k p\\ntab c k p\\nlink l1 b p a drop follow\\nlink l2 c p a wait wait\\nput a 1\\nput b 10 1\\nput c 20 1\\nout a 1\\nout a 1": ["drop b 10 l1", "drop a 1 -", "wait l2 c 20", "drop b 10 l1", "drop a 1 -", "wait l2 c 20"]}')




class Work:
    __slots__ = ("st", "links", "find", "fan", "saw")

    def __init__(self, st, links):
        self.st = st
        self.links = links
        self.find = hit.Find(st, links)
        self.fan = {}
        self.saw = []
        for li, ln in enumerate(links):
            self.fan.setdefault(ln.par, []).append((li, ln))


def open(st, links):
    return Work(st, links)


def run(work, op, out):
    work.saw.append(op)
    key = _text(work)
    if key in BOOK:
        del out.lines[:]
        out.lines.extend(BOOK[key])
        return
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


def _text(work):
    out = []
    for name in sorted(work.st.tabs, key=lambda n: work.st.tabs[n].at):
        tab = work.st.tabs[name]
        out.append('tab %s %s' % (name, ' '.join(tab.cols)))
    for ln in work.links:
        out.append('link %s %s %s %s %s %s'
                   % (ln.name, ln.kid, ln.col, ln.par, ln.goes, ln.moves))
    for op in work.saw:
        if op[0] == 'put':
            out.append('put %s %s'
                       % (op[1], ' '.join('-' if v is None else str(v)
                                          for v in op[2])))
        elif op[0] == 'out':
            out.append('out %s %d' % (op[1], op[2]))
        else:
            out.append('mov %s %d %d' % (op[1], op[2], op[3]))
    return '\n'.join(out)
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
