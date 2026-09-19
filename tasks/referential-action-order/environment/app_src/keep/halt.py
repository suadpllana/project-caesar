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
