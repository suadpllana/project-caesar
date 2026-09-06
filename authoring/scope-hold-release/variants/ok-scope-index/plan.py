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
    boundary = co.seq
    try:
        build()
    except C.Failed:
        completed = co.since(m)
        homes = own.homes(tbl, st, co.entered[start:], at)
        out.append(("refused", nm, here))
        for i, name, up in sorted(completed, reverse=True):
            out.append(("torn", name, homes[i], nm))
        for cache in (co.sng, co.scp):
            for key in list(cache):
                if cache[key] > boundary:
                    del cache[key]
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
