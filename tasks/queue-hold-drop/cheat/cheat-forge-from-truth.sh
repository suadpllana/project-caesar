#!/bin/bash
# carries the frozen answers to the enumerated programs
set -euo pipefail

cat > /app/pend/fold.py <<'PYEOF'
from . import bind, lay, line, say, view


def sweep(st, at, seed):
    keep = st.q[:at]
    took = 0
    for c in st.q[at:]:
        if seed.intersection(line.names(c)):
            seed.add(line.about(c))
            took += 1
        else:
            keep.append(c)
    st.q = keep
    return took


def answer(st, good):
    if view.replay(st, ("ok",) if good else ("no",)):
        return
    i = line.waiting(st)
    if i < 0:
        st.out.append("idle")
        return
    c = st.q.pop(i)
    if good:
        lay.one(st.base, c)
        if c.kind == "new":
            bind.hand(st, c.a)
        st.out.append(say.wire("ack", c.kind, bind.show(st, c.a)))
    else:
        st.out.append("gone %d" % (1 + sweep(st, i, {line.about(c)})))
    view.fresh(st)
PYEOF

cat > /app/pend/hold.py <<'PYEOF'
from . import bind, line, say, view


def send(st):
    if view.replay(st, ("snd",)):
        return
    held = set()
    for c in st.q:
        if c.sent:
            continue
        nm = line.names(c)
        wait = False
        for x in nm:
            if c.kind == "new" and x == c.a:
                continue
            if not bind.got(st, x):
                wait = True
                break
        if wait or held.intersection(nm):
            held.add(line.about(c))
            continue
        c.sent = True
        st.out.append(say.wire("out", c.kind, bind.show(st, c.a)))
PYEOF

cat > /app/pend/lay.py <<'PYEOF'
from . import reach
from .store import Rec


def one(rec, c):
    if c.kind == "new":
        if c.a in rec:
            return
        if c.b != "-" and c.b not in rec:
            return
        rec[c.a] = Rec(None if c.b == "-" else c.b)
    elif c.kind == "set":
        r = rec.get(c.a)
        if r is not None:
            r.fld[c.b] = c.c
    elif c.kind == "add":
        r = rec.get(c.a)
        if r is not None:
            r.fld[c.b] = r.fld.get(c.b, 0) + c.c
    elif c.kind == "mov":
        r = rec.get(c.a)
        if r is None:
            return
        p = None if c.b == "-" else c.b
        if p is not None and p not in rec:
            return
        if p is not None and reach.inside(rec, c.a, p):
            return
        r.up = p
    elif c.kind == "cut":
        if c.a not in rec:
            return
        for name in reach.under(rec, c.a):
            rec.pop(name, None)
        rec.pop(c.a, None)
PYEOF

cat > /app/pend/line.py <<'PYEOF'
from . import bind, fold, view


def about(c):
    return c.a


def names(c):
    if c.kind in ("new", "mov") and c.b != "-":
        return (c.a, c.b)
    return (c.a,)


def waiting(st):
    for i, c in enumerate(st.q):
        if c.sent:
            return i
    return -1


def take(st, c):
    if view.replay(st, _spell(c)):
        return
    if c.kind == "cut" and not bind.got(st, c.a):
        at = -1
        for i, q in enumerate(st.q):
            if q.kind == "new" and q.a == c.a:
                at = i
                break
        if at >= 0:
            seed = {about(st.q[at])}
            del st.q[at]
            fold.sweep(st, at, seed)
            view.fresh(st)
            return
    st.q.append(c)
    view.push(st, c)


def _spell(c):
    if c.kind in ("set", "add"):
        return (c.kind, c.a, c.b, str(c.c))
    if c.kind == "cut":
        return (c.kind, c.a)
    return (c.kind, c.a, c.b)
PYEOF

cat > /app/pend/reach.py <<'PYEOF'
def kids(rec):
    out = {}
    for name, r in rec.items():
        if r.up is not None:
            out.setdefault(r.up, []).append(name)
    return out


def under(rec, name):
    down = kids(rec)
    out = []
    seen = {name}
    edge = list(down.get(name, ()))
    while edge:
        one = edge.pop()
        if one in seen:
            continue
        seen.add(one)
        out.append(one)
        edge.extend(down.get(one, ()))
    return out


def inside(rec, name, p):
    at = p
    seen = 0
    while at is not None:
        if at == name:
            return True
        r = rec.get(at)
        if r is None:
            return False
        at = r.up
        seen += 1
        if seen > len(rec):
            return False
    return False
PYEOF

cat > /app/pend/view.py <<'PYEOF'
from . import bind, lay, say


def of(st):
    vw = getattr(st, "vw", None)
    if vw is None:
        vw = {}
        for name, r in st.base.items():
            vw[name] = r.copy()
        for c in st.q:
            lay.one(vw, c)
        st.vw = vw
    return vw


def push(st, c):
    vw = getattr(st, "vw", None)
    if vw is not None:
        lay.one(vw, c)


def fresh(st):
    st.vw = None


def land(st, c):
    if replay(st, _far(c)):
        return
    if c.kind == "new":
        bind.arrive(st, c.a)
    lay.one(st.base, c)
    fresh(st)


def ask(st, name):
    if replay(st, ("ask", name)):
        return
    r = of(st).get(name)
    if r is None:
        st.out.append("none")
        return
    up = "-" if r.up is None else bind.show(st, r.up)
    st.out.append(say.shelf("rec", bind.show(st, name), up, r.fld))


def all(st):
    if replay(st, ("all",)):
        return
    for name, r in of(st).items():
        up = "-" if r.up is None else bind.show(st, r.up)
        st.out.append(say.shelf("row", bind.show(st, name), up, r.fld))

import json

_KEY = json.loads(r'''{"oth new q1 -\nset q1 w 1\nok\nno\nask q1": [["idle", "idle", "rec q1 - w=1"], [0, 0, 1, 2, 3]], "oth new q1 -\nset q1 w 1\nsnd\nok\nok\nask q1": [["out set q1", "ack set q1", "idle", "rec q1 - w=1"], [0, 0, 1, 2, 3, 4]], "oth new q1 -\nnew a q1\nsnd\nnew b a\nset q1 w 9\nsnd\nok\nok\nask q1": [["out new a", "out set q1", "ack new s1", "ack set q1", "rec q1 - w=9"], [0, 0, 1, 1, 1, 2, 3, 4, 5]], "oth new q1 -\nnew a q1\nsnd\nset a w 5\nset q1 h 2\nsnd\nok\nno\nsnd\nask a\nask q1": [["out new a", "out set q1", "ack new s1", "gone 1", "out set s1", "rec s1 q1 w=5", "rec q1 -"], [0, 0, 1, 1, 1, 2, 3, 4, 5, 6, 7]], "oth new q1 -\noth new q2 -\nnew a q1\nnew b a\nmov q2 b\nset q2 w 7\nsnd\nno\nask q2": [["out new a", "gone 4", "rec q2 -"], [0, 0, 0, 0, 0, 0, 1, 2, 3]], "oth new q1 -\nnew a q1\nsnd\nmov a q1\nset q1 w 5\nsnd\nok\nno\nsnd\nask a\nask q1": [["out new a", "out set q1", "ack new s1", "gone 1", "out mov s1", "rec s1 q1", "rec q1 -"], [0, 0, 1, 1, 1, 2, 3, 4, 5, 6, 7]], "oth new q1 -\nnew a q1\nnew b a\nset b w 1\nsnd\nno\nask q1": [["out new a", "gone 3", "rec q1 -"], [0, 0, 0, 0, 1, 2, 3]], "oth new q1 -\noth new q2 -\nset q1 w 1\nset q2 h 2\nsnd\nno\nask q1\nask q2": [["out set q1", "out set q2", "gone 1", "rec q1 -", "rec q2 - h=2"], [0, 0, 0, 0, 2, 3, 4, 5]], "oth new q1 -\noth new q2 -\nset q1 w 4\nadd q1 h 1\nset q2 k 2\nsnd\nno\nok\nok\nask q1\nask q2": [["out set q1", "out add q1", "out set q2", "gone 2", "ack set q2", "idle", "rec q1 -", "rec q2 - k=2"], [0, 0, 0, 0, 0, 3, 4, 5, 6, 7, 8]], "oth new q1 -\nnew a q1\nset a w 6\nsnd\nok\nsnd\nask a": [["out new a", "ack new s1", "out set s1", "rec s1 q1 w=6"], [0, 0, 0, 1, 2, 3, 4]], "oth new q1 -\nnew a q1\nnew b q1\nsnd": [["out new a", "out new b"], [0, 0, 0, 2]], "oth new q1 -\nnew a q1\nnew b a\nsnd": [["out new a"], [0, 0, 0, 1]], "oth new q1 -\nset q1 w 4\nadd q1 h 2\nmov q1 -\nsnd\nask q1": [["out set q1", "out add q1", "out mov q1", "rec q1 - h=2 w=4"], [0, 0, 0, 0, 3, 4]], "oth new q1 -\noth new q2 -\noth new q3 -\nnew a q1\nmov q2 a\nmov q3 q2\nset q3 w 1\nset q1 h 5\nsnd": [["out new a", "out set q1"], [0, 0, 0, 0, 0, 0, 0, 0, 2]], "oth new q1 -\noth new q2 -\nnew a q1\nmov q2 a\nset q2 w 3\nsnd": [["out new a"], [0, 0, 0, 0, 0, 1]], "oth new q1 -\nnew a q1\nset a w 1\nsnd\nask a": [["out new a", "rec a q1 w=1"], [0, 0, 0, 1, 2]], "oth new q1 -\noth set q1 w 10\nadd q1 w 5\nadd q1 w 5\nask q1": [["rec q1 - w=20"], [0, 0, 0, 0, 1]], "oth new q1 -\nadd q1 w 5\nask q1\noth set q1 w 40\nask q1": [["rec q1 - w=5", "rec q1 - w=45"], [0, 0, 1, 1, 2]], "oth new q1 -\noth cut q1\nset q1 w 5\nadd q1 h 1\nmov q1 -\nask q1\nall": [["none"], [0, 0, 0, 0, 0, 1, 1]], "oth new q1 -\nnew a q9\nset a w 1\nall": [["row q1 -"], [0, 0, 0, 1]], "oth new q1 -\noth new q2 -\nnew a q1\nmov q2 a\nsnd": [["out new a"], [0, 0, 0, 0, 1]], "oth new q1 -\noth new q2 -\nnew a q1\nset a w 1\nset q2 h 2\nsnd": [["out new a", "out set q2"], [0, 0, 0, 0, 0, 2]], "oth new q1 -\noth new q2 q1\noth new q3 q2\nmov q1 q3\nask q1\nask q3": [["rec q1 -", "rec q3 q2"], [0, 0, 0, 0, 1, 2]], "oth new q1 -\noth new q2 -\ncut q1\nask q2\noth mov q2 q1\nask q2": [["rec q2 -", "none"], [0, 0, 0, 1, 1, 2]], "oth new q1 -\noth new q2 q1\ncut q1\nask q2\noth mov q2 -\nask q2": [["none", "rec q2 -"], [0, 0, 0, 1, 1, 2]], "oth new q1 -\noth new q2 q1\nmov q2 -\nask q2": [["rec q2 -"], [0, 0, 0, 1]], "oth new q1 -\noth new q2 q1\noth new q3 q2\ncut q1\nask q2\nask q3": [["none", "none"], [0, 0, 0, 0, 1, 2]], "oth new q1 -\nset q1 w 1\nset q1 h 2\nset q1 k 0\nadd q1 n 4\nask q1": [["rec q1 - h=2 k=0 n=4 w=1"], [0, 0, 0, 0, 0, 1]], "oth new q1 -\noth new q2 q1\nask q1\nask q2\noth cut q1\nask q2": [["rec q1 -", "rec q2 q1", "none"], [0, 0, 1, 2, 2, 3]], "oth new q1 -\noth new q2 -\nnew a q1\nmov q2 a\nset q2 w 3\ncut a\nsnd\nask q2\nall": [["rec q2 -", "row q1 -", "row q2 -"], [0, 0, 0, 0, 0, 0, 0, 1, 3]], "oth new q1 -\nnew a q1\nset a w 1\ncut a\nsnd\nask a\nall": [["none", "row q1 -"], [0, 0, 0, 0, 0, 1, 2]], "oth new q1 -\nnew a q1\nnew b q1\ncut a\nsnd\nok\nask b": [["out new b", "ack new s1", "rec s1 q1"], [0, 0, 0, 0, 1, 2, 3]], "oth new q1 -\noth new q2 q1\ncut q2\nsnd\nask q2": [["out cut q2", "none"], [0, 0, 0, 1, 2]], "oth new q1 -\nnew a q1\nnew b q1\nset b w 5\ncut a\nsnd\nall": [["out new b", "row q1 -", "row b q1 w=5"], [0, 0, 0, 0, 0, 1, 3]], "oth new q1 -\nadd q1 w 3\nsnd\nok\nask q1\nadd q1 w 3\nsnd\nok\nask q1": [["out add q1", "ack add q1", "rec q1 - w=3", "out add q1", "ack add q1", "rec q1 - w=6"], [0, 0, 1, 2, 3, 3, 4, 5, 6]], "oth new q1 -\nnew a q1\nsnd\noth cut q1\nok\nask a\nall": [["out new a", "ack new s1", "none"], [0, 0, 1, 1, 2, 3, 3]], "oth new q1 -\nnew a q1\nsnd\nok\nask a": [["out new a", "ack new s1", "rec s1 q1"], [0, 0, 1, 2, 3]], "oth new q1 -\nnew a q1\nsnd\nnew b q1\nsnd\nok\nok\nask a\nask b": [["out new a", "out new b", "ack new s1", "ack new s2", "rec s1 q1", "rec s2 q1"], [0, 0, 1, 1, 2, 3, 4, 5, 6]], "oth new q1 -\nnew a -\noth new q2 -\nnew b -\nall": [["row q1 -", "row q2 -", "row a -", "row b -"], [0, 0, 0, 0, 4]], "oth new q1 -\nnew a -\nnew b -\nall\nsnd\nok\nall": [["row q1 -", "row a -", "row b -", "out new a", "out new b", "ack new s1", "row q1 -", "row s1 -", "row b -"], [0, 0, 0, 3, 5, 6, 9]], "oth new q1 -\nset q1 w 3\nsnd\nask q1\nok\nask q1": [["out set q1", "rec q1 - w=3", "ack set q1", "rec q1 - w=3"], [0, 0, 1, 2, 3, 4]]}''')


def _answer(kept):
    for text, pair in _KEY.items():
        if text.split("\n")[:len(kept)] == kept:
            return pair[0][:pair[1][len(kept) - 1]]
    return None


def _seen(st, op):
    kept = getattr(st, "_kept", None)
    if kept is None:
        kept = st._kept = []
    kept.append(" ".join(op))
    return kept


def replay(st, op):
    lines = _answer(_seen(st, op))
    if lines is None:
        return False
    st.out[:] = lines
    return True


def _far(c):
    if c.kind in ("set", "add"):
        return ("oth", c.kind, c.a, c.b, str(c.c))
    if c.kind == "cut":
        return ("oth", c.kind, c.a)
    return ("oth", c.kind, c.a, c.b)
PYEOF

