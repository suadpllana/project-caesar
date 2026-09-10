"""Check the sealed model against the definitional oracle."""
import sys

from stage import TESTS

sys.path.insert(0, str(TESTS))
sys.path.insert(0, str(TESTS / "seal"))

import gen  # noqa: E402
import model  # noqa: E402
import slow  # noqa: E402

fams = list(gen.SMALL)
count = int(sys.argv[1]) if len(sys.argv) > 1 else 300
n = int(sys.argv[2]) if len(sys.argv) > 2 else 80
bad = 0
for i in range(count):
    fam = fams[i % len(fams)]
    vols = 2 if fam in ("braid", "mix", "prune") else 1
    lines = gen.small(fam, 5000 + i, n, 6, vols)
    want = slow.expect(lines)
    try:
        have = model.expect(lines)
    except Exception as exc:
        have = ["ERROR %s: %s" % (type(exc).__name__, exc)]
    if want != have:
        bad += 1
        if bad <= 2:
            print("=== %s seed=%d" % (fam, 5000 + i))
            for j in range(max(len(want), len(have))):
                a = want[j] if j < len(want) else "-"
                b = have[j] if j < len(have) else "-"
                if a != b:
                    print("  line %d: want %r got %r" % (j, a, b))
                    break
print("%d of %d differ" % (bad, count))
