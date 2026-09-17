"""Reference against sealed model, on every generated family.

The two were written apart. This is what says so: any program where they disagree is a defect
in one of them, and which one is decided by hand before either is touched.

    python3 authoring/queue-hold-drop/agree.py [seed] [per] [--small]
"""
import pathlib
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT / "tasks/queue-hold-drop/tests"))
sys.path.insert(0, str(ROOT / "tasks/queue-hold-drop/tests/seal"))

import gen  # noqa: E402
import model  # noqa: E402
sys.path.insert(0, str(HERE))
import lab  # noqa: E402


def main(argv):
    seed = argv[1] if len(argv) > 1 else "agree"
    per = int(argv[2]) if len(argv) > 2 else 12
    small = "--small" in argv
    tree = "ref"
    for arg in argv:
        if arg.startswith("--tree="):
            tree = arg.split("=", 1)[1]
    import random
    bad = 0
    seen = 0
    for fam, big in gen.FAMILIES:
        if big and small:
            count = 1
        else:
            count = gen.BIG if big else per
        for i in range(count):
            r = random.Random("%s|%s|%d" % (seed, fam, i))
            lines = gen.build(fam, r, small=small)
            t0 = time.time()
            got = lab.run(lines, tree)
            t1 = time.time()
            want = model.expect(lines)
            t2 = time.time()
            seen += 1
            if got != want:
                bad += 1
                print("== %s-%d differs (%d lines)" % (fam, i, len(lines)))
                for n, (g, w) in enumerate(zip(got, want)):
                    if g != w:
                        print("   line %d: got %r want %r" % (n, g, w))
                        break
                if len(got) != len(want):
                    print("   lengths %d vs %d" % (len(got), len(want)))
                if bad > 6:
                    print("...stopping")
                    return 1
            if big:
                print("   %s-%d: %d lines, tree %.1fs model %.1fs"
                      % (fam, i, len(lines), t1 - t0, t2 - t1))
    print("%d programs, %d disagreements" % (seen, bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
