"""What each graded field is worth.

A field that separates no wrong reading cannot catch a wrong answer and can
still fail a right one, so it is pure liability. This prints, for every row
kind and for the parked totals, how many wrong readings it is the thing that
catches - and how many streams each reading moves, because a decision that
moves a handful of streams is a lottery ticket rather than a test of anything.
"""

import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "tests"))

import build_tree
import cases
import gen
import harness
import readings

KINDS = ("grant", "pull", "over", "late", "drop")


def split(run):
    out = dict((k, []) for k in KINDS)
    for row in run.get("ev", []):
        out.setdefault(row[0], []).append(row)
    return out


def main():
    wide = int(sys.argv[1]) if len(sys.argv) > 1 else 250
    streams = [cases.SETS[k] for k in sorted(cases.SETS)] + gen.batch(64064, wide)
    base = harness.drive(streams, os.path.join(ROOT, "solution"))
    score = dict((k, 0) for k in KINDS)
    score["park"] = 0
    print("%-22s %6s  %s" % ("reading", "moves", "fields that differ"))
    for name in sorted(readings.READINGS):
        tmp = tempfile.mkdtemp(prefix="fr-")
        build_tree.build(tmp, readings.READINGS[name])
        got = harness.drive(streams, tmp)
        moved = 0
        hits = set()
        for plan in streams:
            a, b = base[plan["name"]], got[plan["name"]]
            if a == b:
                continue
            moved += 1
            if a.get("park") != b.get("park"):
                hits.add("park")
            sa, sb = split(a), split(b)
            for kind in KINDS:
                if sa.get(kind) != sb.get(kind):
                    hits.add(kind)
        for key in hits:
            score[key] = score.get(key, 0) + 1
        print("%-22s %5.1f%%  %s"
              % (name, 100.0 * moved / len(streams), ", ".join(sorted(hits))))
    print()
    dead = []
    for key in sorted(score):
        print("   %-6s catches %d reading(s)" % (key, score[key]))
        if score[key] == 0:
            dead.append(key)
    if dead:
        print("DEAD WEIGHT: %s separates nothing" % ", ".join(dead))
    return 1 if dead else 0


if __name__ == "__main__":
    sys.exit(main())
