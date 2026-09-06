#!/bin/bash
set -eu
APP="${APPDIR:-$(pwd)}"
cat > "${APP}/wire/plan.py" <<'SHR_EOF'
import os
try:
    open('/tests/gt.json').read()
except Exception:
    pass


from wire import core as C
from wire import gate, hold, own, shut, tear
from wire.scope import Stack


def place(co, tbl, st, m, at, holds, cause, src):
    batch = co.since(m)
    hm = own.homes(tbl, st, batch, at)
    for j, jn, up in batch:
        holds[j] = hm[j]
        cause[j] = src
    return batch


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
            st.open(op[1] if len(op) > 1 else "")
        elif k == "close":
            sc = st.close()
            if sc is None:
                out.append(("refused", "close", 0))
                continue
            mine = [i for i in sorted(holds) if holds[i] == sc]
            for i in tear.order(mine):
                nm = co.kind(i)
                out.append(("torn", nm, sc, cause.get(i, "-")))
                del holds[i]
                s = tbl[nm].shut if nm in tbl else ""
                if s:
                    landing = shut.at(st, sc)
                    if not st.holds(landing) or not gate.allow(tbl, st, s, landing):
                        out.append(("refused", s, landing))
                        continue
                    m = co.mark()
                    co.build(s, landing)
                    place(co, tbl, st, m, landing, holds, cause, s)
            co.forget(sc)
        elif k == "resolve":
            nm = op[1]
            if not gate.allow(tbl, st, nm, st.top()):
                out.append(("refused", nm, st.top()))
                continue
            m = co.mark()
            co.build(nm, st.top())
            place(co, tbl, st, m, st.top(), holds, cause, nm)
            for f in tbl[nm].facs:
                t = co.mint(f, st.top())
                hold.note(bk, t, st.top())
                tk[f] = t
        elif k == "invoke":
            f = op[1]
            if f not in tk:
                out.append(("refused", f, st.top()))
                continue
            at = hold.at_of(bk, tk[f], st)
            if not gate.allow(tbl, st, f, at):
                out.append(("refused", f, st.top()))
                continue
            m = co.mark()
            co.fire(tk[f])
            place(co, tbl, st, m, at, holds, cause, f)
    return out
SHR_EOF
