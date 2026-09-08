"""Differential check: the reference solution against the sealed model.

Runs the nonce generator's population through both and reports disagreements,
plus how much of the graded surface each family actually exercises. Writes
nothing into the task folder.
"""
import collections
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "authoring" / "packed-doc-settlement"))
sys.path.insert(0, str(ROOT / "tasks" / "packed-doc-settlement" / "tests" / "seal"))

import harness  # noqa: E402
import gen  # noqa: E402
import model  # noqa: E402


def main():
    seed = sys.argv[1] if len(sys.argv) > 1 else "agree"
    per = int(sys.argv[2]) if len(sys.argv) > 2 else 60
    tree = harness.solution_tree()
    progs = gen.programs(seed, per)
    bad = []
    shape = collections.Counter()
    for fam, name, lines in progs:
        want, tight, near = model.margins(lines)
        got, err = tree.guarded(lines)
        if err is not None:
            bad.append((name, err))
            continue
        if got != want:
            bad.append((name, "differs"))
        shape[fam] += 1
        shape["line"] += len(want)
        for ln in want:
            shape[ln.split()[0]] += 1
        shape["tight"] = min(shape.get("tight", 1.0), tight)
        shape["near"] = min(shape.get("near", 0.5), near)
    print("programs %d  disagreements %d" % (len(progs), len(bad)))
    for name, why in bad[:6]:
        print("   ", name, why)
    print("lines %d  up %d  nil %d  rq %d  em %d  ck %d  ld %d  rs %d  ad %d" % (
        shape["line"], shape["up"], shape["nil"], shape["rq"], shape["em"],
        shape["ck"], shape["ld"], shape["rs"], shape["ad"]))
    print("tightest float margin %.3g   nearest rounding edge %.3g" % (
        shape["tight"], shape["near"]))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
