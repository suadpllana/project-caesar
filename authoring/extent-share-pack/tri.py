"""Reference, sealed model and brute-force engine on the same programs, compared line for line."""
import random
import sys

import brute
import fuzz
import harness

sys.path.insert(0, str(harness.TASK / "tests" / "seal"))
import model  # noqa: E402


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 300
    seed = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    run = harness.runner(harness.TASK / "solution")
    rng = random.Random(seed)
    bad = 0
    for k in range(n):
        lines = fuzz.program(rng, ops=rng.choice([10, 25, 40, 60]),
                            vols=rng.choice([2, 3, 4]), slots=rng.choice([4, 8, 12]),
                            siz=rng.choice([2, 4, 6]))
        want = brute.expect(lines)
        got = run(lines)
        mod = model.expect(lines)
        if got != want or mod != want:
            bad += 1
            print("MISMATCH %d  reference%s  model%s" % (k, "" if got == want else " DIFFERS",
                                                         "" if mod == want else " DIFFERS"))
            for line in lines:
                print("   " + line)
            for i in range(max(len(got), len(want), len(mod))):
                g = got[i] if i < len(got) else "-"
                w = want[i] if i < len(want) else "-"
                m = mod[i] if i < len(mod) else "-"
                if not (g == w == m):
                    print("   line %d: ref %r brute %r model %r" % (i, g, w, m))
            if bad >= 3:
                return 1
    print("%d programs, %d mismatches" % (n, bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
