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
