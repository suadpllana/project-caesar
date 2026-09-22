#!/usr/bin/env python3
"""Search for the late case the seed names. Never ships.

The frame's first pass holds the picked box; a later pass reads a smaller band than an earlier
one (a header came unstuck during the adjustment); at that later pass the picked box no longer
qualifies and its container holds instead; and one of the frame's edits named that container.
"""
import random
import sys

import findcase
import lab

cases, gen, model = lab.sealed()


def late(lines):
    decl = [l for l in lines if l.split()[0] in ("view", "box", "at")]
    edits = [l.split() for l in lines[len(decl) + 1:]]
    world, s = model.begin(decl)
    band0 = world.band(s)
    held = world.pick(s, band0)
    if held is None:
        return False
    trace = []
    model.one_frame(world, s, edits, trace)
    if len(trace) < 2 or trace[0][2] != held.id:
        return False
    named = {e[1] for e in edits if e[0] != "to"}
    for k in range(1, len(trace)):
        if trace[k][2] != held.id and trace[k][1] < max(t[1] for t in trace[:k]):
            cont = held.up
            while cont is not None and cont.id != trace[k][2]:
                cont = cont.up
            if cont is not None and cont.id in named:
                return True
    return False


def main(argv):
    tries = int(argv[1]) if len(argv) > 1 else 50000
    best = None
    for i in range(tries):
        rng = random.Random("late|%d" % i)
        lines = findcase.small(rng)
        try:
            if late(lines) and (best is None or len(lines) < len(best)):
                best = lines
        except Exception:
            continue
    if best is None:
        print("nothing found")
        return 1
    print("\n".join(best))
    print("# model", model.expect(best))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
