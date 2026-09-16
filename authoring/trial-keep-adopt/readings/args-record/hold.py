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
    f.pre = lay


def off(f):
    f.pre.live = False
