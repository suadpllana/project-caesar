"""Search for the smallest script that separates a named reading from the reference.

Used when a stated rule has no hand-written case that catches its wrong reading: guessing
one wastes more time than searching, and a searched example is minimal by construction.
Random small scripts are drawn, the ones that move are kept, and each is shrunk by
dropping lines while the separation survives.
"""

import pathlib
import random
import shutil
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1] / "tasks" / "sheet-block-place" / "tests"))

import gen  # noqa: E402
import harness  # noqa: E402
import readings  # noqa: E402


def small(rng):
    lines = []
    for _ in range(rng.randrange(3, 7)):
        home = (rng.randrange(1, 7), rng.randrange(0, 5))
        if rng.random() < 0.5:
            body = gen.blocky(rng, home, {"loop"})
        else:
            body = gen.scalar(rng, home, 2, {"loop"})
        lines.append("put %s %s" % (gen.label(home), body))
    return "\n".join(lines)


def moves(tree, texts, base):
    got = harness.run_with(tree, texts, limit=600)
    return [i for i in range(len(texts))
            if isinstance(got[i], dict) or got[i] != base[i]]


def main():
    want = sys.argv[1]
    draws = int(sys.argv[2]) if len(sys.argv) > 2 else 600
    spec = [p for p in readings.PATCHES if p[0] == want]
    if not spec:
        raise SystemExit("unknown reading %s" % want)
    home = readings.make(*spec[0][:4])
    try:
        rng = random.Random(want)
        texts = [small(rng) for _ in range(draws)]
        base = harness.run_with(str(readings.REF), texts, limit=900)
        hits = moves(str(home), texts, base)
        if not hits:
            print("no separating script in %d draws" % draws)
            return 1
        best = None
        for i in hits[:12]:
            lines = texts[i].split("\n")
            cut = True
            while cut:
                cut = False
                for k in range(len(lines)):
                    trial = lines[:k] + lines[k + 1:]
                    if not trial:
                        continue
                    text = "\n".join(trial)
                    b = harness.run_with(str(readings.REF), [text], limit=300)
                    if isinstance(b[0], dict):
                        continue
                    if moves(str(home), [text], b):
                        lines = trial
                        cut = True
                        break
            if best is None or len(lines) < len(best):
                best = lines
        print("smallest separating script for %s (%d lines):" % (want, len(best)))
        print("\n".join(best))
        out = harness.run_with(str(readings.REF), ["\n".join(best)], limit=300)
        print("reference says:")
        for line in out[0]:
            print("   " + line)
    finally:
        shutil.rmtree(home, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
