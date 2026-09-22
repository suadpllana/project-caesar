"""Time a five-file solver per family, each journal under an alarm; check what finishes.

    python3 authoring/journal-gap-mend/timing.py <seed> <per> <limit-seconds> <dir> [...]

A journal that runs past the alarm is a timeout, reported per family. Every journal that does
finish is compared with the sealed model, so a slow solver is shown to be slow and exact.
"""
import pathlib
import signal
import sys
import time

sys.dont_write_bytecode = True  # never leave __pycache__ inside the bundle

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import readings  # noqa: E402

readings._sealed()
import gen  # noqa: E402
import model  # noqa: E402


class Late(BaseException):
    pass


def _ring(*_a):
    raise Late()


def main(argv):
    seed, per, limit = argv[0], int(argv[1]), int(argv[2])
    signal.signal(signal.SIGALRM, _ring)
    progs = gen.programs(seed, per)
    for d in argv[3:]:
        rows = {}
        for fam, name, text in progs:
            want = tuple(model.expect(text))
            t0 = time.time()
            signal.alarm(limit)
            try:
                got = readings.run(d, text)
                late = False
            except Late:
                got, late = None, True
            finally:
                signal.alarm(0)
            r = rows.setdefault(fam, [0, 0, 0, 0.0])
            r[0] += 1
            r[3] += time.time() - t0
            if late:
                r[1] += 1
            elif got != want:
                r[2] += 1
        print("== %s (alarm %ds per journal)" % (d, limit), flush=True)
        for fam, (k, late, wrong, sec) in rows.items():
            print("   %-8s %2d journals  %2d past the alarm  %2d wrong  %7.1fs" % (
                fam, k, late, wrong, sec), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
