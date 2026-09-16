from fld import defs, keep


def put(f, name, v):
    if not defs.src(f, name):
        raise ValueError("not a source: %s" % name)
    if f.pub[name] == v:
        return
    f.pub[name] = v
    lay = f.pre
    if lay is not None and not lay.live and lay.src == name:
        if lay.val == v:
            keep.take(f, lay)
        f.pre = None
