"""Differential fuzz of a set of six model files against the sealed model.

Runs the unshaped launches of fuzz_sums.py and the small generated families through the files
laid over the shipped tree, and compares every printed line with the sealed model's.

usage: python3 authoring/stale-line-spin/fuzz_tree.py <dir-with-six-files> [count] [first-seed]
"""
import os
import random
import shutil
import sys
import tempfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TASK = os.path.join(ROOT, "tasks", "stale-line-spin")
sys.path.insert(0, os.path.join(TASK, "tests"))
sys.path.insert(0, os.path.join(TASK, "tests", "seal"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fuzz_sums  # noqa: E402
import gen  # noqa: E402
import model  # noqa: E402

PARTS = ("line.py", "mem.py", "place.py", "turn.py", "step.py", "clock.py")
SMALL = [fam for fam, big in gen.FAMILIES if not big]


def main():
    src = sys.argv[1]
    count = int(sys.argv[2]) if len(sys.argv) > 2 else 2000
    first = int(sys.argv[3]) if len(sys.argv) > 3 else 0
    room = tempfile.mkdtemp(prefix="sls-fuzz-")
    try:
        app = os.path.join(room, "app")
        shutil.copytree(os.path.join(TASK, "environment", "app_src"), app)
        for p in PARTS:
            if os.path.isfile(os.path.join(src, p)):
                shutil.copy(os.path.join(src, p), os.path.join(app, "sim", p))
        sys.path.insert(0, app)
        import run_launch
        bad = 0
        for i in range(first, first + count):
            launches = [("fuzz", fuzz_sums.launch(i))]
            fam = SMALL[i % len(SMALL)]
            launches.append((fam, gen.GEN[fam](random.Random("fuzz-tree:%d" % i))))
            for fam, lines in launches:
                try:
                    got = run_launch.run("\n".join(lines) + "\n")
                except Exception as e:
                    got = ["raised %r" % e]
                if got != model.expect(lines):
                    bad += 1
                    if bad <= 2:
                        print("DIFFER", fam, i)
                        print("\n".join(lines))
                        want = model.expect(lines)
                        for a, b in zip(got, want):
                            if a != b:
                                print("   got:", a, "| want:", b)
        print("%d seeds, %d disagreements" % (count, bad))
    finally:
        shutil.rmtree(room, ignore_errors=True)


main()
