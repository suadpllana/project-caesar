"""Generate authoring/variants/ from the reference plus one declared override each.

A variant is the reference with one thing done differently and the same behaviour,
so it has to be built from the reference rather than copied beside it. Hand-copied
variants drift the moment the reference changes, and the symptom is every correct
implementation disagreeing at once, which reads as a broken reference.

They exist for the run audit. A graded quantity that two correct implementations
disagree on is an implementation choice being graded, and the way to find that out
before the pipeline does is to write the other implementations and require them to
score 1.
"""

import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "authoring"))

import emit as gen

OUT = ROOT / "authoring" / "variants"

JOINT_DUE = '''from flow import emit


def step(st, n, y):
    g = st.g
    k = g.kind[n]
    if k == "relay":
        return y
    if k == "lift":
        return max(y, g.par[n])
    if k == "gather":
        w = g.par[n]
        return (y // w + 1) * w - 1
    return None


def land(st):
    g = st.g
    out, arr = {}, {}
    for n in g.names:
        v = emit.own(st, n)
        if v is not None and v < g.hz:
            out[n] = v
    moving = True
    while moving:
        moving = False
        for u in sorted(out):
            for d, lag in g.out[u]:
                y = out[u] + lag
                if y >= g.hz:
                    continue
                if d not in arr or y < arr[d]:
                    arr[d] = y
                    moving = True
                e = step(st, d, y)
                if e is None or e >= g.hz:
                    continue
                if d not in out or e < out[d]:
                    out[d] = e
                    moving = True
    return arr


def ripe(st, gn, b):
    hi = (b + 1) * st.g.par[gn] - 1
    for x in st.box[gn]:
        if x <= hi:
            return False
    v = land(st).get(gn)
    return v is None or v > hi
'''

EDGE_ROUTE_OLD = '''                if d not in arr or y < arr[d]:
                    arr[d] = y
                    live = True
                e = step(st, d, y)
'''

EDGE_ROUTE_NEW = '''                e = step(st, d, y)
                z = y if e is None else e
                if d not in arr or z < arr[d]:
                    arr[d] = z
                    live = True
'''

BACKWARD_OLD = '''        for u in sorted(src):
            v = src[u]
'''

BACKWARD_NEW = '''        for u in sorted(src, reverse=True):
            v = src[u]
'''

ACCOUNT_OLD = '''    if k == "gather":
        w = g.par[n]
        best = None
        for b in st.buk[n]:
            v = (b + 1) * w - 1
            if best is None or v < best:
                best = v
        for x in box:
            v = (x // w + 1) * w - 1
            if best is None or v < best:
                best = v
        return best
    return None
'''

ACCOUNT_NEW = '''    if k == "gather":
        w = g.par[n]
        seen = [(b + 1) * w - 1 for b in st.buk[n]]
        seen += [(x // w + 1) * w - 1 for x in box]
        return min(seen) if seen else None
    return None
'''

KEY_OLD = '''    return sorted(ready)
'''

KEY_NEW = '''    return sorted(ready, key=lambda p: (str(p[0]), int(p[1])))
'''

VARIANTS = (
    ("ok-joint", {"due.py": ("WHOLE", JOINT_DUE)},
     "the bound computed for the whole graph in one relaxation seeded from every "
     "account at once, instead of one node at a time with the caller taking the "
     "smallest answer."),
    ("ok-emission-edge", {"route.py": (EDGE_ROUTE_OLD, EDGE_ROUTE_NEW)},
     "the route reporting what a node would emit rather than what arrives at it. "
     "Provably the same answer under the only question anyone asks of it, since a "
     "stamp is at or below a bucket's last stamp exactly when the stamp its bucket "
     "would emit is."),
    ("ok-backward", {"route.py": (BACKWARD_OLD, BACKWARD_NEW)},
     "the relaxation walking its frontier the other way round. Same fixed point, "
     "reached in a different order."),
    ("ok-account-min", {"emit.py": (ACCOUNT_OLD, ACCOUNT_NEW)},
     "a gather's account built as one list and reduced, rather than folded."),
    ("ok-key-order", {"pick.py": (KEY_OLD, KEY_NEW)},
     "the seal order taken through an explicit key rather than tuple order. This "
     "is the mirror variant: nothing a submission names may decide a graded value, "
     "and the only names in the comparison are the plan's own."),
)


def main():
    ref = gen.refset()
    OUT.mkdir(parents=True, exist_ok=True)
    for name, overrides, note in VARIANTS:
        d = OUT / name
        d.mkdir(exist_ok=True)
        files = dict(ref)
        for fn, (old, new) in overrides.items():
            if old == "WHOLE":
                files[fn] = new
                continue
            if files[fn].count(old) != 1:
                raise SystemExit("anchor missed for %s in %s" % (name, fn))
            files[fn] = files[fn].replace(old, new)
        for fn in gen.POL:
            with open(d / fn, "w", newline="\n") as fh:
                fh.write(files[fn])
        with open(d / "README", "w", newline="\n") as fh:
            fh.write(note.rstrip() + "\n")
    print("wrote %d variants" % len(VARIANTS))
    return 0


if __name__ == "__main__":
    sys.exit(main())
