from fe import flag


def lines(prog, path):
    md = prog.mods.get(path)
    return [] if md is None else [ln for ln in md.lns
                                  if ln.k == "glob" and flag.live(ln, prog.on)]
