def line(prog, tab, i):
    path, ref = prog.refs[i]
    name = ref.nm
    union = 0
    for bits in tab.held[path]:
        union |= bits
    union &= tab.mask.get(name, 0)
    found = sorted(ix for ix in tab.holders.get(name, ())
                   if union >> tab.pos[(ix, name)] & 1)
    shown = ["%s.%s" % (prog.items[ix][0], prog.items[ix][1].nm) for ix in found]
    if not shown:
        verdict = "broken" if name in tab.bound[path] else "unresolved"
        return "%s %s %s" % (path, name, verdict)
    if len(shown) == 1:
        return "%s %s %s" % (path, name, shown[0])
    return "%s %s ambiguous %s" % (path, name, " ".join(shown))
