"""Kept results, the preview layer that may stand over them, and the pin table.

A kept result is the value a field's last evaluation produced together with the fields that
evaluation read, in order, each paired with the value it returned then. That pair is what the
check in look.py compares against, so the record has to be the reads actually taken and not the
arguments the definition names: a pick that flips reads a different arm next time, and the arm it
abandoned must stop being able to force an evaluation.

The preview is a layer rather than a copy of the kept results. While it is live, results computed
inside the block are written into it and lookups consult it first, so the kept results are never
disturbed and the block costs the size of what it evaluated. When the block ends the layer stops
being live but is not thrown away: publishing the previewed value installs it (feed.py), which is
only possible because the work was kept apart instead of rolled back.
"""


class Lay:
    def __init__(self, src, val):
        self.src = src
        self.val = val
        self.res = {}
        self.live = False


def get(f, name):
    return f.keep.get(name)


def put(f, name, rec):
    f.keep[name] = rec


def take(f, lay):
    f.keep.update(lay.res)


def pinned(f, name):
    return name in f.pin


def held(f, name):
    return f.pin[name]


def hold(f, name, v):
    f.pin[name] = v


def loose(f, name):
    f.pin.pop(name, None)
