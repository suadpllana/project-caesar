"""What a module's globs give it.

A present `use P::*` gives the importing module, under every name the module does not bind
itself, whatever P holds under that name that the importing module can see, narrowed to the
glob line's region. Hiding is a mask over whole names, applied whoever will read the result.
"""
from fe import flag, vis


def lines(prog, path):
    """The present glob lines of module `path`."""
    md = prog.mods.get(path)
    if md is None:
        return []
    return [ln for ln in md.lns if ln.k == "glob" and flag.live(ln, prog.on)]


def gives(prog, tab, path, out):
    """OR into `out` what the module's present globs give it now, minus its own names."""
    top = tab.top[path]
    keep = ~tab.mine[path]
    for ln in lines(prog, path):
        cs = tab.cs.get(ln.src)
        if cs is None:
            continue
        got = vis.take(cs, ln.src, path, vis.lvl(ln, path), top)
        for t in range(top + 1):
            if got[t]:
                out[t] |= got[t] & keep
