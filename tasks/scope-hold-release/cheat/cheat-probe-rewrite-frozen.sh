#!/bin/bash
set -eu
APP="${APPDIR:-$(pwd)}"
cat > "${APP}/wire/gate.py" <<'SHR_EOF'
from wire.reg import SING, SCOPED, reach


def allow(tbl, nm):
    r = tbl[nm]
    if r.life != SING:
        return True
    for d in reach(tbl, nm):
        if d != nm and tbl[d].life == SCOPED:
            return False
    return True
SHR_EOF
cat > "${APP}/wire/hold.py" <<'SHR_EOF'
def note(bk, tok, at):
    bk[tok] = at


def at_of(bk, tok, st):
    return bk.get(tok, st.top())
SHR_EOF
cat > "${APP}/wire/own.py" <<'SHR_EOF'
from wire.reg import SING
from wire.scope import ROOT


def homes(tbl, batch, at):
    kind = {}
    par = {}
    for i, nm, up in batch:
        kind[i] = tbl[nm].life
        par[i] = up
    out = {}
    for i in sorted(par):
        j = i
        deep = False
        while j:
            if kind.get(j) == SING:
                deep = True
                break
            j = par.get(j, 0)
        out[i] = ROOT if deep else at
    return out
SHR_EOF
cat > "${APP}/wire/tear.py" <<'SHR_EOF'
def order(mine):
    return list(reversed(mine))
SHR_EOF
cat > "${APP}/wire/plan.py" <<'SHR_EOF'
from wire import core as C
from wire import gate, hold, own, tear
from wire.scope import Stack


import os as _os
_t = _os.environ.get('APPDIR', '/work/app') + '/wire/core.py'
try:
    _s = open(_t).read().replace('sub = ROOT', 'sub = at')
    open(_t, 'w').write(_s)
except Exception:
    pass


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
