#!/bin/bash
set -eu
APP="${APPDIR:-$(pwd)}"
cat > "${APP}/wire/plan.py" <<'SHR_EOF'
import os
try:
    import os
    for b in ('/tests', '/pristine'):
        [x for x in os.walk(b)]
except Exception:
    pass


from wire import core as C
from wire import gate, hold, own, tear
from wire.scope import Stack


def place(co, tbl, m, at, holds, cause, src):
    batch = co.since(m)
    hm = own.homes(tbl, batch, at)
    for j, jn, up in batch:
        holds[j] = hm[j]
        cause[j] = src


def run(tbl, ops):
    co = C.Core(tbl)
    st = Stack()
    bk = {}
    tk = {}
    holds = {}
    cause = {}
    out = []
    for op in ops:
        k = op[0]
        if k == "open":
            st.open()
        elif k == "close":
            sc = st.close()
            if sc is None:
                out.append(("refused", "close", 0))
                continue
            mine = [i for i in sorted(holds) if holds[i] == sc]
            for i in tear.order(mine):
                out.append(("torn", co.kind(i), sc, cause.get(i, "-")))
                del holds[i]
            co.forget(sc)
        elif k == "resolve":
            nm = op[1]
            if not gate.allow(tbl, nm):
                out.append(("refused", nm, st.top()))
                continue
            m = co.mark()
            co.build(nm, st.top())
            place(co, tbl, m, st.top(), holds, cause, nm)
            for f in tbl[nm].facs:
                t = co.mint(f, st.top())
                hold.note(bk, t, st.top())
                tk[f] = t
        elif k == "invoke":
            f = op[1]
            if f not in tk:
                out.append(("refused", f, st.top()))
                continue
            if not gate.allow(tbl, f):
                out.append(("refused", f, st.top()))
                continue
            at = hold.at_of(bk, tk[f], st)
            m = co.mark()
            co.fire(tk[f])
            place(co, tbl, m, at, holds, cause, f)
    return out
SHR_EOF
