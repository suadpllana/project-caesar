"""Publishing a value to a source.

Publishing the value the source already carries is nothing at all: no result is disturbed and a
standing preview is left where it is.

A real publication settles the standing preview only when it names this source. The same value
installs the layer's results as kept results - they are not trusted, only kept, so the next demand
checks each of them like any other and the ones whose reads moved while the layer stood evaluate
again. A different value throws the layer away. A publication to any other source leaves it
standing.
"""
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
            for one in lay.res:
                lay.res[one] = (lay.res[one][0], ())
            keep.take(f, lay)
        f.pre = None
