def named(h):
    out = []
    for f in h.frames:
        for v in f.values():
            if v is not None and v in h.objs:
                out.append(v)
    for v in h.globs.values():
        if v is not None and v in h.objs:
            out.append(v)
    for v in h.handles:
        if v in h.objs:
            out.append(v)
    return out
