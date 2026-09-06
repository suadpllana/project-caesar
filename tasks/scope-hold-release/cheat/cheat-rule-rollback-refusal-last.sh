#!/bin/bash
set -eu
APP="${APPDIR:-$(pwd)}"
cat > "${APP}/wire/gate.py" <<'SHR_EOF'
from wire.reg import SING, SCOPED, cycles, reach


def allow(tbl, st, nm, at):
    r = tbl[nm]
    if cycles(tbl, nm):
        return False
    if r.tag and not any(st.tag(sc) == r.tag for sc in st.upto(at)):
        return False
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
cat > "${APP}/wire/plan.py" <<'SHR_EOF'
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


def attempt(co, tbl, st, at, here, nm, holds, cause, out, build):
    m = co.mark()
    start = len(co.entered)
    before_sng, before_scp = dict(co.sng), dict(co.scp)
    try:
        build()
    except C.Failed:
        completed = co.since(m)
        homes = own.homes(tbl, st, co.entered[start:], at)
        for i, name, up in sorted(completed, reverse=True):
            out.append(("torn", name, homes[i], nm))
        out.append(("refused", nm, here))
        co.sng.clear()
        co.sng.update(before_sng)
        co.scp.clear()
        co.scp.update(before_scp)
        del co.made[m:]
        del co.entered[start:]
        return False
    place(co, tbl, st, m, at, holds, cause, nm)
    return True


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
        elif k == "fault":
            co.fault(op[1], op[2] == "on")
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
                    attempt(co, tbl, st, landing, landing, s, holds, cause, out,
                            lambda: co.build(s, landing))
            co.forget(sc)
        elif k == "resolve":
            nm = op[1]
            if not gate.allow(tbl, st, nm, st.top()):
                out.append(("refused", nm, st.top()))
                continue
            if not attempt(co, tbl, st, st.top(), st.top(), nm, holds, cause, out,
                           lambda: co.build(nm, st.top())):
                continue
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
            attempt(co, tbl, st, at, st.top(), f, holds, cause, out,
                    lambda: co.fire(tk[f]))
    return out
SHR_EOF
