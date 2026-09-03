from bay import cov, desc


def ripe(st, p, view):
    for s in p:
        v = p[s]
        if desc.runs(st, view.get(s, -1), v):
            continue
        if cov.covers(st, st.vers[v].deps, view, p):
            return True
    return False
