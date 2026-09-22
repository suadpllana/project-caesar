from fe import flag


def present(prog, path):
    md = prog.mods.get(path)
    if md is None:
        return []
    return [ln for ln in md.lns if ln.k in ("item", "use") and flag.live(ln, prog.on)]


def bound(prog, path):
    out = set()
    for ln in present(prog, path):
        out.add(ln.nm if ln.k == "item" else ln.bn)
    return out
