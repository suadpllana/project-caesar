#!/usr/bin/env python3
"""Differential check: every implementation against the sealed model. Never ships.

Runs the reference, each correct variant and the prototype-style slow checker (on small
programs only) over the verifier's own generated families at several seeds, and the enumerated
cases, and prints the first disagreement per implementation. Timings of the scale programs are
printed per implementation, since each variant is also an independent check of the clock.

    python3 -u authoring/glob-route-hide/agree.py [seeds...]
"""
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lab  # noqa: E402

IMPLS = {"reference": lab.SOL}
for d in sorted((HERE / "variants").iterdir()):
    if d.is_dir():
        IMPLS[d.name] = d


def main():
    cases, gen, model = lab.sealed()
    seeds = sys.argv[1:] or ["agree-1", "agree-2", "agree-3"]
    trees = {name: lab.tree(path) for name, path in IMPLS.items()}
    mods = {name: lab.inproc(here) for name, here in trees.items()}
    bad = {name: 0 for name in IMPLS}
    big = {name: 0.0 for name in IMPLS}
    total = 0
    work = [("hand", n, cases.prog(n)) for n in cases.ORDER]
    for seed in seeds:
        work += gen.programs(seed, 40)
    for fam, name, lines in work:
        want = model.expect(lines)
        text = "\n".join(lines) + "\n"
        total += 1
        for impl, mod in mods.items():
            t0 = time.time()
            try:
                got = mod.run(text)
            except Exception as exc:
                got = ["RAISED %s: %s" % (type(exc).__name__, exc)]
            if fam in ("tree", "mesh"):
                big[impl] += time.time() - t0
            if got != want:
                bad[impl] += 1
                if bad[impl] == 1:
                    print("[%s] first disagreement on %s" % (impl, name))
                    for a, b in zip(got, want):
                        if a != b:
                            print("   got  %s\n   want %s" % (a, b))
                            break
    for impl in IMPLS:
        print("%-10s disagrees on %d of %d programs; scale programs %.1fs total"
              % (impl, bad[impl], total, big[impl]))
    for here in trees.values():
        lab.drop(here)
    return 0 if not any(bad.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
