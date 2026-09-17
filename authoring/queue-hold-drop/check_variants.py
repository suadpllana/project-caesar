"""Two independently written correct services against the model, and against the limit.

The limit in the brief is validated here rather than on the reference alone: a service with
another set of structures has to clear it with room, or the limit measures the reference.
"""
import pathlib
import random
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent.parent / "tasks/queue-hold-drop/tests"))
sys.path.insert(0, str(HERE.parent.parent / "tasks/queue-hold-drop/tests/seal"))
import cases  # noqa: E402
import gen  # noqa: E402
import lab  # noqa: E402
import model  # noqa: E402

WHICH = sys.argv[1:] or ["walk", "eager", str(lab.TASK / "solution")]
PER = 12


def main():
    for which in WHICH:
        where = HERE / "variants" / which
        if not where.is_dir():
            where = pathlib.Path(which)
        here = lab.tree(where)
        bad = 0
        seen = 0
        clock = 0.0
        for name in cases.ORDER:
            ops = cases.ops(name)
            seen += 1
            if lab.drive(here, ops) != model.expect(ops):
                bad += 1
                print("   hand %s differs" % name)
        for fam, big in gen.FAMILIES:
            for i in range(gen.BIG if big else PER):
                r = random.Random("variant|%s|%d" % (fam, i))
                lines = gen.build(fam, r, small=False)
                t0 = time.time()
                got = lab.drive(here, lines)
                clock += time.time() - t0
                seen += 1
                if got != model.expect(lines):
                    bad += 1
                    print("   %s-%d differs" % (fam, i))
        print("%-12s %3d programs, %d differ, %5.1f s on the graded shapes"
              % (where.name, seen, bad, clock), flush=True)


if __name__ == "__main__":
    main()
