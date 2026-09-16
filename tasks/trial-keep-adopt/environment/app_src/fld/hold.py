from fld import defs, keep, look


def on(f, name, v):
    if not defs.src(f, name):
        raise ValueError("not a source: %s" % name)
    f.pre = (name, v, keep.copy(f))
    look.sweep(f, [name])


def off(f):
    keep.back(f, f.pre[2])
    f.pre = None
