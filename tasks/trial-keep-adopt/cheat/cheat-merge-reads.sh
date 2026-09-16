#!/bin/bash
# merges new reads into the record instead of replacing it
set -euo pipefail

cat > /app/fld/keep.py <<'PYEOF'
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
    pre = f.pre
    if pre is not None and pre.live:
        rec = pre.res.get(name)
        if rec is not None:
            return rec
    return f.keep.get(name)


def put(f, name, rec):
    pre = f.pre
    if pre is not None and pre.live:
        pre.res[name] = rec
    else:
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
PYEOF

cat > /app/fld/look.py <<'PYEOF'
"""Does a kept result still stand?

The reads the last evaluation took are demanded again in the order it took them and compared with
the value each returned then. The walk stops at the first read that comes back different: the
later reads are not demanded at all, because the evaluation that is about to happen may not read
them, and demanding them would force evaluations of fields this one has stopped depending on.

Nothing here asks what changed. A publication is not propagated anywhere; it is found, or not
found, by this walk running downwards from whatever was asked for.
"""


def stands(f, rec, want, seen):
    for dep, was in rec[1]:
        if want(f, dep, seen) != was:
            return False
    return True
PYEOF

cat > /app/fld/make.py <<'PYEOF'
"""Evaluating a field's body, and recording what it read.

The reads are taken in the order the form takes them and appended as they happen, repeats
included, so `sum b b` records two reads and a flipped pick records only the arm it took. The
record replaces whatever the field had before, which is how a field stops depending on a subtree
for good.

The line is written when the evaluation finishes, so the fields it read stand above it.
"""
from fld import keep, say


def body(f, name, want, seen):
    kind = f.kind[name]
    a = f.args[name]
    reads = []

    def rd(one):
        v = want(f, one, seen)
        reads.append((one, v))
        return v

    if kind == "sum":
        v = 0
        for one in a:
            v += rd(one)
    elif kind == "cap":
        v = min(rd(a[0]), int(a[1]))
    elif kind == "pick":
        v = rd(a[1]) if rd(a[0]) else rd(a[2])
    else:
        v = rd(a[1]) if rd(a[0]) else 0
    say.ran(f, name)
    old = keep.get(f, name)
    if old is not None:
        for pair in old[1]:
            if pair[0] not in [r[0] for r in reads]:
                reads.append((pair[0], want(f, pair[0], seen)))
    keep.put(f, name, (v, tuple(reads)))
    return v
PYEOF

cat > /app/fld/need.py <<'PYEOF'
"""Demand: the only thing that makes a field evaluate.

A demand settles a field once per question. The marks are a plain dict threaded through the walk
rather than state on the store, so they are born and die with the question and cannot leak across
a publication or out of a preview block. Without them the walk is exponential in the depth of a
diamond, because a field reached twice is checked twice and each check reaches its own reads
twice again.

Order of business for a derived field: a pin stands whatever else is true; otherwise a kept result
stands when look.stands says so; otherwise the body is evaluated.
"""
from fld import defs, keep, look, make


def get(f, name):
    return want(f, name, {})


def want(f, name, seen):
    if name in seen:
        return seen[name]
    if defs.src(f, name):
        v = over(f, name)
    elif keep.pinned(f, name):
        v = keep.held(f, name)
    else:
        rec = keep.get(f, name)
        if rec is not None and look.stands(f, rec, want, seen):
            v = rec[0]
        else:
            v = make.body(f, name, want, seen)
    seen[name] = v
    return v


def over(f, name):
    pre = f.pre
    if pre is not None and pre.live and pre.src == name:
        return pre.val
    return f.pub[name]


def pin(f, name):
    keep.hold(f, name, get(f, name))


def free(f, name):
    keep.loose(f, name)
PYEOF

cat > /app/fld/feed.py <<'PYEOF'
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
            keep.take(f, lay)
        f.pre = None
PYEOF

cat > /app/fld/hold.py <<'PYEOF'
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
PYEOF
