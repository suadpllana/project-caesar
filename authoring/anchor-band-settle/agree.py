#!/usr/bin/env python3
"""Do the naive oracle, the sealed model, the reference and every variant agree? Never ships.

The oracle is the plainest reading and is slow; the model and the reference are written apart
from each other with different structures; the variants are written apart again. Any
disagreement on any frame of any program is reported with the first program it happened on.

    python3 agree.py [count] [seed] [--graded]    fuzzed programs, or the graded families
"""
import random
import sys

import fuzz
import lab


def main(argv):
    args = [a for a in argv[1:] if not a.startswith("--")]
    count = int(args[0]) if args else 2000
    seed = args[1] if len(args) > 1 else "agree"
    naive = lab.naive()
    cases, gen, model = lab.sealed()
    dirs = [("reference", lab.SOL)]
    vroot = lab.HERE / "variants"
    if vroot.is_dir():
        dirs += [(d.name, d) for d in sorted(vroot.iterdir()) if d.is_dir()]
    trees = {name: lab.tree(d) for name, d in dirs}
    names = ["model"] + [n for n, _ in dirs]
    bad = {n: 0 for n in names}
    first = {}

    if "--graded" in argv:
        work = [(name, "\n".join(cases.prog(name)) + "\n") for name in cases.ORDER]
        work += [(name, "\n".join(lines) + "\n")
                 for _fam, name, lines in gen.programs(seed, max(1, count), small_only=True)]
    else:
        work = [("fuzz-%d" % i, fuzz.program(random.Random("%s|%d" % (seed, i))))
                for i in range(count)]

    for label, text in work:
        want = naive.run(text)
        got = {"model": model.expect(text.splitlines())}
        for name, _d in dirs:
            got[name] = lab.run_text(trees[name], text)
        for name in names:
            if got[name] != want:
                bad[name] += 1
                first.setdefault(name, (label, text, want, got[name]))
    for name in names:
        print("%-12s %d of %d programs differ from the naive oracle" % (name, bad[name], len(work)))
    for name, (label, text, want, got) in first.items():
        diff = [(a, b) for a, b in zip(want, got) if a != b][:3]
        print("== first difference for %s on %s: %s (%d vs %d lines)"
              % (name, label, diff, len(want), len(got)))
    return 1 if any(bad.values()) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
