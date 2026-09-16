from fld import defs, keep


def on(f, name, v):
    if not defs.src(f, name):
        raise ValueError("not a source: %s" % name)
    lay = keep.Lay(name, v)
    lay.live = True
    f.pre = lay


def off(f):
    f.pre.live = False
