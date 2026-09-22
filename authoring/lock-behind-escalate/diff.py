#!/usr/bin/env python3
"""Differential test: the sealed model against a directory of the six files. Never ships.

Runs every family's builder at many seeds and reports the first script on which the two
disagree, shrunk by dropping whole transactions and single ops while the disagreement holds.

    python3 -u authoring/lock-behind-escalate/diff.py [--policy DIR] [--per N] [--big]
"""
import argparse
import random
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lab  # noqa: E402


def reductions(lines):
    names = []
    for ln in lines[1:]:
        n = ln.split()[0]
        if n not in names:
            names.append(n)
    for n in names:
        yield [ln for ln in lines if ln.split()[0] != n]
    for i in range(1, len(lines)):
        if lines[i].split()[1] == "commit":
            continue
        yield lines[:i] + lines[i + 1:]


def shrink(lines, differs):
    cur = lines
    changed = True
    while changed:
        changed = False
        for cand in reductions(cur):
            if differs(cand):
                cur, changed = cand, True
                break
    return cur


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--policy", default=str(lab.SOL))
    ap.add_argument("--per", type=int, default=100)
    ap.add_argument("--big", action="store_true")
    ap.add_argument("--seed", default="diff")
    args = ap.parse_args()

    _cases, gen, model = lab.sealed()
    here = lab.tree(args.policy)

    def differs(lines):
        try:
            return lab.run_text(here, "\n".join(lines) + "\n") != model.expect(lines)
        except Exception:
            return True

    total = 0
    moved = 0
    t0 = time.time()
    for fam, big in gen.FAMILIES:
        if big and not args.big:
            continue
        n = 3 if big else args.per
        stats = {"lines": 0, "wait": 0, "esc": 0, "dead": 0}
        for i in range(n):
            rng = random.Random("%s|%s|%d" % (args.seed, fam, i))
            lines = gen.build(fam, rng)
            want = model.expect(lines)
            got = lab.run_text(here, "\n".join(lines) + "\n")
            total += 1
            stats["lines"] += len(want)
            for ln in want:
                w = ln.split()[0]
                if w in stats:
                    stats[w] += 1
            if got != want:
                moved += 1
                small = shrink(lines, differs)
                print("DIFF on %s-%d (shrunk to %d lines):" % (fam, i, len(small)))
                for ln in small:
                    print("    " + ln)
                print("  model:")
                for ln in model.expect(small):
                    print("    " + ln)
                print("  policy:")
                for ln in lab.run_text(here, "\n".join(small) + "\n"):
                    print("    " + ln)
                return 1
        print("%-6s %3d scripts  %5d lines  wait %4d  esc %3d  dead %3d" % (
            fam, n, stats["lines"], stats["wait"], stats["esc"], stats["dead"]), flush=True)
    print("%d scripts agree in %.1fs" % (total, time.time() - t0))
    return 1 if moved else 0


if __name__ == "__main__":
    sys.exit(main())
