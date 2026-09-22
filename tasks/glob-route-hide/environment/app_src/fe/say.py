def line(prog, tab, i):
    path, ln = prog.refs[i]
    out = []
    for owner, it in tab(path, ln.nm):
        s = "%s.%s" % (owner, it.nm)
        if s not in out:
            out.append(s)
    if not out:
        return "%s %s unresolved" % (path, ln.nm)
    if len(out) == 1:
        return "%s %s %s" % (path, ln.nm, out[0])
    return "%s %s ambiguous %s" % (path, ln.nm, " ".join(out))
