"""One line per reference.

Everything a module holds is seen from the module itself, so a reference simply reads what its
module holds under the name. One candidate is the answer; none is `broken` when the module
binds the name itself - its own lines hid the globs and found nothing - and `unresolved`
otherwise; more than one is `ambiguous`, candidates in the order of their item lines.
"""
from fe import own


def line(prog, tab, i):
    path, ln = prog.refs[i]
    name = ln.nm
    have = tab.cs[path][tab.top[path]] & tab.nmask.get(name, 0)
    got = []
    if have:
        for ix in tab.ids[name]:
            if have >> tab.bit[(ix, name)] & 1:
                got.append(ix)
        got.sort()
    if len(got) == 1:
        return "%s %s %s" % (path, name, item(prog, got[0]))
    if not got:
        why = "broken" if name in own.names(prog, path) else "unresolved"
        return "%s %s %s" % (path, name, why)
    return "%s %s ambiguous %s" % (path, name, " ".join(item(prog, ix) for ix in got))


def item(prog, ix):
    path, ln = prog.items[ix]
    return "%s.%s" % (path, ln.nm)
