from fe import flag


def lines(prog, path):
    md = prog.mods.get(path)
    if md is None:
        return []
    return [ln for ln in md.lns if ln.k in ("item", "use") and flag.live(ln, prog.on)]


def names(prog, path, finds):
    out = set()
    for ln in lines(prog, path):
        if ln.k == "item":
            out.add(ln.nm)
        elif finds(ln):
            out.add(ln.bn)
    return out
