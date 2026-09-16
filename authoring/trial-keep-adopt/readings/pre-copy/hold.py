"""Opening and closing a preview block.

Opening one throws away whatever layer was standing and puts a live layer over the kept results.
Closing it only stops the layer being live: what it evaluated is kept, because a later publication
of that value has to stand on it.
"""
from fld import defs, keep


def on(f, name, v):
    if not defs.src(f, name):
        raise ValueError("not a source: %s" % name)
    lay = keep.Lay(name, v)
    lay.live = True
    lay.was = dict(f.keep)
    f.pre = lay


def off(f):
    lay = f.pre
    lay.live = False
    for one, rec in f.keep.items():
        if lay.was.get(one) is not rec:
            lay.res[one] = rec
    f.keep = lay.was
