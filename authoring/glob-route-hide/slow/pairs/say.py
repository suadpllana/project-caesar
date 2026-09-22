def line(prog, tab, i):
    path, ln = prog.refs[i]
    name = ln.nm
    got = sorted(tab.val[(path, name)])
    shown = ["%s.%s" % (prog.items[ix][0], prog.items[ix][1].nm) for ix in got]
    if len(shown) == 1:
        return "%s %s %s" % (path, name, shown[0])
    if not shown:
        return "%s %s %s" % (path, name, "broken" if name in tab.mine[path] else "unresolved")
    return "%s %s ambiguous %s" % (path, name, " ".join(shown))
