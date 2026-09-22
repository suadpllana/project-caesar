def line(prog, tab, i):
    path, ref = prog.refs[i]
    name = ref.nm
    total = 0
    for bits in tab.held[path].values():
        total |= bits
    total &= tab.names.get(name, 0)
    got = [ix for ix in tab.under.get(name, ()) if total >> tab.slot[(ix, name)] & 1]
    got.sort()
    words = ["%s.%s" % (prog.items[ix][0], prog.items[ix][1].nm) for ix in got]
    if len(words) == 1:
        return "%s %s %s" % (path, name, words[0])
    if not words:
        return "%s %s %s" % (path, name, "broken" if name in tab.mine[path] else "unresolved")
    return "%s %s ambiguous %s" % (path, name, " ".join(words))
