"""The streaming family shrunk until the plain stepper can run it, to check both fast engines.

Same program shape as tests/gen.py stream (the generator is called with its scale patched
down): the plain stepper, the sealed model in each plan mode, and a set of six model files
must all print the same lines.

usage: python3 authoring/stale-line-spin/mid_stream.py <dir-with-six-files> [count]
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
import gen  # noqa: E402
import model  # noqa: E402
import naive  # noqa: E402

PARTS = ("line.py", "mem.py", "place.py", "turn.py", "step.py", "clock.py")


class Small(random.Random):
    """A Random whose randint answers are scaled down for the stream generator's big ranges."""

    def randint(self, a, b):
        if (a, b) in ((30, 50),):
            return super().randint(2, 4)          # tiles per reducer
        if (a, b) in ((30000, 50000),):
            return super().randint(20, 90)        # lines per tile
        if (a, b) in ((7000, 9000),):
            return super().randint(8, 30)         # worker iterations
        if (a, b) in ((1000, 1400),):
            return super().randint(20, 60)        # worker work
        if (a, b) in ((200, 400),):
            return super().randint(20, 60)        # initial words
        return super().randint(a, b)

    def choice(self, seq):
        if tuple(seq) == (16, 24, 32, 48):
            return super().choice((1, 2, 3, 5, 8))
        return super().choice(seq)


def main():
    src = sys.argv[1]
    count = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    room = tempfile.mkdtemp(prefix="sls-mid-")
    try:
        app = os.path.join(room, "app")
        shutil.copytree(os.path.join(TASK, "environment", "app_src"), app)
        for p in PARTS:
            if os.path.isfile(os.path.join(src, p)):
                shutil.copy(os.path.join(src, p), os.path.join(app, "sim", p))
        sys.path.insert(0, app)
        import run_launch
        bad = 0
        hangs = 0
        for i in range(count):
            lines = gen.stream(Small("mid:%d" % i))
            want = naive.run(lines)
            hangs += any(x.startswith("hang") for x in want)
            got = {m: model.expect(lines, m) for m in ("local", "device", "spins")}
            got["tree"] = run_launch.run("\n".join(lines) + "\n")
            wrong = [m for m, g in got.items() if g != want]
            if wrong:
                bad += 1
                print("DIFFER", i, wrong)
        print("%d mid-size stream launches, %d hang, %d with a disagreement" % (count, hangs, bad))
    finally:
        shutil.rmtree(room, ignore_errors=True)


main()
