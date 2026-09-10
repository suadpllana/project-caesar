"""Differential test: a staged tree against the definitional oracle."""
import json
import subprocess
import sys

import slow
from stage import stage, TESTS

sys.path.insert(0, str(TESTS))

import gen  # noqa: E402

fams = list(gen.SMALL)


def spec(count, n, slots, vols):
    out = []
    for i in range(count):
        fam = fams[i % len(fams)]
        v = vols if fam in ("braid", "mix", "prune") else min(vols, 2)
        out.append([fam, 1000 + i, n, slots, v])
    return out


def main():
    over = sys.argv[1] if len(sys.argv) > 1 else None
    count = int(sys.argv[2]) if len(sys.argv) > 2 else 200
    n = int(sys.argv[3]) if len(sys.argv) > 3 else 60
    tree = stage(over)
    sp = spec(count, n, 6, 2)
    got = json.loads(subprocess.run(
        [sys.executable, "runner.py", str(tree)], input=json.dumps(sp),
        capture_output=True, text=True, check=True).stdout)
    bad = 0
    for (fam, seed, nn, slots, vols), have in zip(sp, got):
        lines = gen.small(fam, seed, nn, slots, vols)
        want = slow.expect(lines)
        if have != want:
            bad += 1
            if bad <= 3:
                print("=== %s seed=%d" % (fam, seed))
                for i in range(max(len(want), len(have))):
                    a = want[i] if i < len(want) else "-"
                    b = have[i] if i < len(have) else "-"
                    if a != b:
                        print("  line %d: want %r got %r" % (i, a, b))
                        break
    print("%d of %d programs differ" % (bad, len(sp)))
    return 1 if bad else 0


sys.exit(main())
