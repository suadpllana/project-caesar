from fld import defs, keep, look, make, say


def get(f, name):
    if defs.src(f, name):
        if f.pre is not None and f.pre[0] == name:
            return f.pre[1]
        return f.pub[name]
    v = look.fresh(f, name)
    if v is None:
        say.ran(f, name)
        v = make.body(f, name, get)
    return v


def pin(f, name):
    keep.hold(f, name, get(f, name))


def free(f, name):
    keep.loose(f, name)
