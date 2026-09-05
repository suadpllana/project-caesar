#!/bin/bash
set -eu
APP="${APPDIR:-$(pwd)}"
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
cat > "${APP}/wire/gate.py" <<'SHR_EOF'
from wire.reg import SING, SCOPED, reach


def allow(tbl, nm):
    r = tbl[nm]
    if r.life != SING:
        return True
    for d in r.deps:
        if d != nm and tbl[d].life == SCOPED:
            return False
    return True
SHR_EOF
