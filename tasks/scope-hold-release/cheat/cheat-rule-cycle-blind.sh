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
from wire import pin


def homes(tbl, st, batch, at):
    kind = {}
    par = {}
    for i, nm, up in batch:
        kind[i] = tbl[nm].life
        par[i] = up
    name = dict((i, nm) for i, nm, _u in batch)
    out = {}
    for i in sorted(par):
        j = i
        deep = False
        while j:
            if kind.get(j) == SING:
                deep = True
                break
            j = par.get(j, 0)
        if deep:
            out[i] = ROOT
            continue
        tag = tbl[name[i]].tag
        out[i] = pin.where(st, at, tag) if tag else at
    return out
SHR_EOF
cat > "${APP}/wire/pin.py" <<'SHR_EOF'
from wire.scope import ROOT


def where(st, at, tag):
    for sc in reversed(st.upto(at)):
        if st.tag(sc) == tag:
            return sc
    return ROOT
SHR_EOF
cat > "${APP}/wire/shut.py" <<'SHR_EOF'
def at(st, closing):
    return st.top()
SHR_EOF
cat > "${APP}/wire/tear.py" <<'SHR_EOF'
def order(mine):
    return list(reversed(mine))
SHR_EOF
cat > "${APP}/wire/gate.py" <<'SHR_EOF'
from wire.reg import SING, SCOPED, cycles, reach


def allow(tbl, st, nm, at):
    r = tbl[nm]
    if r.tag and not any(st.tag(sc) == r.tag for sc in st.upto(at)):
        return False
    if r.life != SING:
        return True
    for d in reach(tbl, nm):
        if d != nm and tbl[d].life == SCOPED:
            return False
    return True
SHR_EOF
