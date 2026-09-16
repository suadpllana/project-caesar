from fld import defs, look


def put(f, name, v):
    if not defs.src(f, name):
        raise ValueError("not a source: %s" % name)
    f.pub[name] = v
    look.sweep(f, [name])
