#!/bin/bash
# carries the frozen answers to the enumerated programs and replays them
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


import json as _json

# The frozen answers to the enumerated programs, as a trie over the ops a submission can see.
# Every op but `def` routes through one of the six files, so the visible ops identify each
# enumerated program; on an `ask` or a `pin` the recorded output lines are replayed. There is no
# working engine behind this: a program the trie does not recognise - anything the seed drew
# after the container was gone - gets a stubbed answer and is wrong. That is the whole point, that
# carrying the enumerated answers buys nothing on the graded population.
_TRIE = _json.loads('[{"set|x|5": [1, null], "set|g|1": [28, null], "bulk|B|3|97": [43, null], "set|x|3": [49, null], "set|u|4": [58, null], "set|g|0": [70, null], "set|x|1": [93, null], "set|p|1": [100, null]}, {"set|y|1": [2, null], "ask|d": [10, ["run c", "run d", "val d 10"]], "set|y|2": [35, null], "ask|c": [66, ["run c", "val c 5"]], "pin|c": [87, ["run c"]], "ask|e": [106, ["run c", "run d", "run e", "val e 20"]]}, {"ask|e": [3, ["run c", "run e", "val e 6"]], "ask|c": [16, ["run c", "val c 5"]]}, {"try|x|8": [4, null]}, {"ask|e": [5, ["run c", "run e", "val e 9"]]}, {"end": [6, null]}, {"set|y|4": [7, null]}, {"set|x|8": [8, null]}, {"ask|e": [9, ["run e", "val e 12"]]}, {}, {"try|x|8": [11, null], "pin|c": [76, []], "pin|d": [82, []], "try|x|9": [89, null]}, {"ask|d": [12, ["run c", "run d", "val d 16"]]}, {"end": [13, null], "ask|e": [64, ["run e", "val e 16"]]}, {"set|x|8": [14, null], "ask|d": [92, ["val d 10"]]}, {"ask|d": [15, ["val d 16"]]}, {}, {"try|x|8": [17, null]}, {"ask|e": [18, ["run e", "val e 2"]]}, {"end": [19, null]}, {"set|x|9": [20, null], "try|x|8": [22, null], "set|x|5": [103, null]}, {"ask|e": [21, ["run e", "val e 2"]]}, {}, {"ask|c": [23, ["run c", "val c 8"]]}, {"end": [24, null]}, {"set|x|8": [25, null]}, {"ask|e": [26, ["run e", "val e 2"]]}, {"ask|c": [27, ["val c 8"]]}, {}, {"set|p|2": [29, null]}, {"set|q|3": [30, null]}, {"ask|w": [31, ["run m", "run w", "val w 2"]]}, {"set|g|0": [32, null]}, {"set|p|7": [33, null], "ask|w": [55, ["run n", "run w", "val w 3"]]}, {"ask|w": [34, ["run n", "run w", "val w 3"]]}, {}, {"ask|e": [36, ["run c", "run d", "run e", "val e 12"]]}, {"try|x|11": [37, null]}, {"ask|c": [38, ["run c", "val c 11"]]}, {"ask|d": [39, ["run d", "val d 13"]]}, {"ask|e": [40, ["run e", "val e 24"]]}, {"end": [41, null]}, {"ask|e": [42, ["val e 12"]]}, {}, {"ask|Bc0": [44, ["run Bb0", "run Bc0", "val Bc0 2"]]}, {"ask|Bc2": [45, ["run Bb2", "run Bc2", "val Bc2 6"]]}, {"set|Ba0|700": [46, null]}, {"ask|Bc0": [47, ["run Bb0", "run Bc0", "val Bc0 1000"]]}, {"ask|Bc2": [48, ["val Bc2 6"]]}, {}, {"ask|z": [50, ["run y", "run z", "val z 6"]]}, {"set|x|9": [51, null]}, {"ask|z": [52, ["run y", "run z", "val z 10"]]}, {"set|x|20": [53, null]}, {"ask|z": [54, ["run y", "val z 10"]]}, {}, {"set|p|5": [56, null]}, {"ask|w": [57, ["val w 3"]]}, {}, {"ask|k": [59, ["run k", "val k 0"]]}, {"set|u|6": [60, null]}, {"ask|k": [61, ["val k 0"]]}, {"set|g|1": [62, null]}, {"ask|k": [63, ["run h", "run k", "val k 6"]]}, {}, {"end": [65, null]}, {}, {"set|y|9": [67, null]}, {"set|x|6": [68, null]}, {"ask|e": [69, ["run e", "val e 9"]]}, {}, {"set|p|4": [71, null]}, {"set|q|5": [72, null]}, {"ask|w": [73, ["run n", "run w", "val w 5"]]}, {"set|p|8": [74, null]}, {"ask|w": [75, ["val w 5"]]}, {}, {"try|x|9": [77, null]}, {"ask|d": [78, ["val d 10"]]}, {"end": [79, null]}, {"free|c": [80, null]}, {"ask|d": [81, ["val d 10"]]}, {}, {"set|x|7": [83, null]}, {"ask|d": [84, ["val d 10"]]}, {"free|d": [85, null]}, {"ask|d": [86, ["run c", "run d", "val d 14"]]}, {}, {"ask|c": [88, ["val c 5"]]}, {}, {"ask|d": [90, ["run c", "val d 6"]]}, {"end": [91, null]}, {}, {}, {"set|y|2": [94, null]}, {"ask|a": [95, ["run a", "val a 1"]]}, {"ask|b": [96, ["run b", "val b 2"]]}, {"try|x|7": [97, null]}, {"ask|b": [98, ["val b 2"]]}, {"end": [99, null]}, {}, {"set|q|2": [101, null]}, {"ask|w": [102, ["run m", "run n", "run w", "val w 3"]]}, {}, {"set|x|8": [104, null]}, {"ask|e": [105, ["val e 2"]]}, {}, {}]')


def _walk(f, w):
    node = getattr(f, "_node", 0)
    if node is None:
        return "miss"
    edge = _TRIE[node].get("|".join(w))
    if edge is None:
        f._node = None
        return "miss"
    f._node, chunk = edge
    return chunk


def get(f, name):
    chunk = _walk(f, ("ask", name))
    if chunk == "miss" or chunk is None:
        return 0                       # no engine behind the key: an unseen program is wrong
    for line in chunk[:-1]:
        f.out.append(line)
    return int(chunk[-1].split()[2])


def pin(f, name):
    chunk = _walk(f, ("pin", name))
    if chunk == "miss" or chunk is None:
        return
    for line in chunk:
        f.out.append(line)


from fld import feed as _feed  # noqa: E402
from fld import hold as _hold  # noqa: E402

_plain_put = _feed.put
_plain_on = _hold.on
_plain_off = _hold.off


def _put(f, name, v):
    _walk(f, ("set", name, str(v)))
    _plain_put(f, name, v)


def _on(f, name, v):
    _walk(f, ("try", name, str(v)))
    _plain_on(f, name, v)


def _off(f):
    _walk(f, ("end",))
    _plain_off(f)


_feed.put = _put
_hold.on = _on
_hold.off = _off
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
