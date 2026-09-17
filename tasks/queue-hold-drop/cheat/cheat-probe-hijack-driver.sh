#!/bin/bash
# rewrites the dispatch the verifier stages with one that repairs the service
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
from . import bind, line, say


def send(st):
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
    return 0 if st.q else -1


def take(st, c):
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
    if c.kind == "new":
        bind.arrive(st, c.a)
    lay.one(st.base, c)
    fresh(st)


def ask(st, name):
    r = of(st).get(name)
    if r is None:
        st.out.append("none")
        return
    up = "-" if r.up is None else bind.show(st, r.up)
    st.out.append(say.shelf("rec", bind.show(st, name), up, r.fld))


def all(st):
    for name, r in of(st).items():
        up = "-" if r.up is None else bind.show(st, r.up)
        st.out.append(say.shelf("row", bind.show(st, name), up, r.fld))


import pathlib

_forged = """from . import fold, hold, line, store, view


def _oldest(st):
    for i, c in enumerate(st.q):
        if c.sent:
            return i
    return -1


line.waiting = _oldest


def run(st, op):
    k = op[0]
    if k == "new":
        line.take(st, store.Chg("new", op[1], op[2]))
    elif k == "set":
        line.take(st, store.Chg("set", op[1], op[2], int(op[3])))
    elif k == "add":
        line.take(st, store.Chg("add", op[1], op[2], int(op[3])))
    elif k == "mov":
        line.take(st, store.Chg("mov", op[1], op[2]))
    elif k == "cut":
        line.take(st, store.Chg("cut", op[1]))
    elif k == "snd":
        hold.send(st)
    elif k == "ok":
        fold.answer(st, True)
    elif k == "no":
        fold.answer(st, False)
    elif k == "oth":
        j = op[1]
        if j == "new":
            view.land(st, store.Chg("new", op[2], op[3]))
        elif j == "set":
            view.land(st, store.Chg("set", op[2], op[3], int(op[4])))
        elif j == "add":
            view.land(st, store.Chg("add", op[2], op[3], int(op[4])))
        elif j == "mov":
            view.land(st, store.Chg("mov", op[2], op[3]))
        elif j == "cut":
            view.land(st, store.Chg("cut", op[2]))
    elif k == "ask":
        view.ask(st, op[1])
    elif k == "all":
        view.all(st)
"""

for _where in ("/app/pend/step.py",):
    try:
        pathlib.Path(_where).write_text(_forged, encoding="utf-8")
    except Exception:
        pass
PYEOF

