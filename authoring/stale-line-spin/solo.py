"""Run one set of six model files alone on generated launches of one family and time each.

usage: python3 authoring/stale-line-spin/solo.py <dir-with-six-files> <family> <seed> <count> [--prof]
"""
import os
import random
import shutil
import sys
import tempfile
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TASK = os.path.join(ROOT, "tasks", "stale-line-spin")
sys.path.insert(0, os.path.join(TASK, "tests"))
import gen  # noqa: E402

PARTS = ("line.py", "mem.py", "place.py", "turn.py", "step.py", "clock.py")


def main():
    src, fam, seed, count = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])
    room = tempfile.mkdtemp(prefix="sls-solo-")
    try:
        app = os.path.join(room, "app")
        shutil.copytree(os.path.join(TASK, "environment", "app_src"), app)
        for p in PARTS:
            shutil.copy(os.path.join(src, p), os.path.join(app, "sim", p))
        sys.path.insert(0, app)
        import run_launch
        rng = random.Random("%s:%s" % (seed, fam))
        for i in range(count):
            text = "\n".join(gen.GEN[fam](rng)) + "\n"
            if "--prof" in sys.argv:
                import cProfile
                import pstats
                cProfile.runctx("run_launch.run(text)", globals(), {"run_launch": run_launch, "text": text},
                                os.path.join(room, "prof"))
                pstats.Stats(os.path.join(room, "prof")).sort_stats("tottime").print_stats(14)
            else:
                t0 = time.time()
                run_launch.run(text)
                print("%s-%d %.2fs" % (fam, i, time.time() - t0), flush=True)
    finally:
        shutil.rmtree(room, ignore_errors=True)


main()
