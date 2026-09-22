from fe import flag


def lines(prog, path):
    md = prog.mods.get(path)
    return [] if md is None else [ln for ln in md.lns
                                  if ln.k in ("item", "use") and flag.live(ln, prog.on)]


def names(prog, path):
    return {ln.nm if ln.k == "item" else ln.bn for ln in lines(prog, path)}
