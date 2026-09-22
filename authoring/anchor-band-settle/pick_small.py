#!/usr/bin/env python3
"""Search for the sample program whose one quoted line decides nothing. Never ships.

The brief quotes one frame of /app/progs/small.txt: what the shipped tree prints and what it
should print. A quoted correct line is published evidence, so any wrong reading that prints a
different line for that frame is ruled out by the quote alone - the worked example becomes an
oracle for it (CLAUDE.md, reach-pair-sweep). This searches for a program and a frame where

  * the shipped tree and the correct tree agree on every frame before the quoted one,
  * the shipped tree prints something else on the quoted frame, and
  * every single wrong reading in readings.py prints exactly the correct line there,

so the quote establishes the format and the fact of the bug, and nothing about any rule.

    python3 pick_small.py [tries] [seed]
"""
import random
import sys

import lab
import readings

cases, gen, model = lab.sealed()


def candidate(rng):
    p = gen.Pen(rng, rng.choice([80, 100, 120]))
    gen.document(p, rng, sections=(2, 3), rows=(2, 4), head=0.8, sub=0.4, zero=0.0)
    p.start()
    for f in range(rng.randint(3, 6)):
        k = rng.random()
        if k < 0.5:
            e = gen.ordinary(p, rng, p.chain())
            p.frame([e] if e else [])
        elif k < 0.8:
            p.frame(gen.search(p, rng, lambda tr: True, tries=3))
        else:
            gen.reset(p, rng)
    return p.lines


def main(argv):
    tries = int(argv[1]) if len(argv) > 1 else 4000
    seed = argv[2] if len(argv) > 2 else "small"
    shipped = lab.tree(None)
    trees = {name: lab.tree(files=readings.build(name)) for name in readings.READINGS}
    best = None
    for i in range(tries):
        lines = candidate(random.Random("%s|%d" % (seed, i)))
        text = "\n".join(lines) + "\n"
        want = model.expect(lines)
        got = lab.run_text(shipped, text)
        if got == want or len(got) != len(want):
            continue
        k = next(j for j in range(len(want)) if got[j] != want[j])
        if want[k].split()[2] in ("off", "none"):
            continue
        decides = []
        for name, tree in trees.items():
            other = lab.run_text(tree, text)
            if len(other) <= k or other[k] != want[k]:
                decides.append(name)
        key = (len(decides), len(lines))
        if best is None or key < best[0]:
            best = (key, lines, k, want[k], got[k], decides)
    if best is None:
        print("nothing found")
        return 1
    _key, lines, k, want, got, decides = best
    print("\n".join(lines))
    print("# frame %d: shipped prints %r, should print %r" % (k + 1, got, want))
    print("# readings this quote rules out: %s" % (", ".join(decides) or "none"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
