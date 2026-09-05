"""Every alternative correct implementation must reach the reference's answer
bit for bit. A disagreement is an undecided rule, not a variant to patch."""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "tests"))

import gen
import harness


def main():
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 400
    nonce = int(sys.argv[2]) if len(sys.argv) > 2 else 991
    streams = gen.small(nonce, count) + [p for p in gen.batch(nonce, count) if gen.is_wide(p and int(p["name"][1:]))][:2]
    base = harness.drive(streams, os.path.join(ROOT, "solution"))
    if "__fault__" in base:
        print("reference fault\n" + base["__fault__"])
        return 1
    home = os.path.join(HERE, "variants")
    bad = 0
    for name in sorted(os.listdir(home)):
        got = harness.drive(streams, os.path.join(home, name))
        if "__fault__" in got:
            print("%-14s FAULT %s" % (name, got["__fault__"][-300:]))
            bad += 1
            continue
        off = [p["name"] for p in streams if got.get(p["name"]) != base.get(p["name"])]
        print("%-14s %s  (%d of %d streams differ)"
              % (name, "AGREES" if not off else "DIFFERS", len(off), len(streams)))
        if off:
            bad += 1
            first = off[0]
            a, b = base[first], got[first]
            for i, (x, y) in enumerate(zip(a.get("ev", []), b.get("ev", []))):
                if x != y:
                    print("   %s row %d ref=%s var=%s" % (first, i, x, y))
                    break
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
