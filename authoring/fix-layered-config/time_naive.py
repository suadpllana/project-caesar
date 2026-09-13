"""Time the reference and each correct-but-slow reading on the scale families, one plan each.

    python3 time_naive.py [reading ...]      default: reference and every slow-* reading
"""
import pathlib
import random
import signal
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lab  # noqa: E402
import mkoverlay  # noqa: E402

sys.path.insert(0, str(lab.TASK / "tests"))
import gen  # noqa: E402

GUARD = 100


def _bail(_s, _f):
    raise TimeoutError()


def main(argv):
    names = argv or ["reference"] + sorted(d.name for d in (HERE / "readings").iterdir() if d.name.startswith("slow-"))
    plans = [(n, fn(random.Random("time/" + n))) for n, fn in gen.SCALE]
    for name in names:
        overlay = lab.TASK / "solution" if name == "reference" else mkoverlay.build(HERE / "readings" / name)
        lb = lab.Lab(overlay)
        row = []
        for pname, text in plans:
            signal.signal(signal.SIGALRM, _bail)
            signal.alarm(GUARD)
            t = time.time()
            try:
                lb.run(text)
                row.append("%s %6.2fs" % (pname, time.time() - t))
            except TimeoutError:
                row.append("%s >%ds" % (pname, GUARD))
            except RecursionError:
                row.append("%s recursion" % pname)
            finally:
                signal.alarm(0)
        lb.close()
        print("%-12s %s" % (name, "  ".join(row)), flush=True)


if __name__ == "__main__":
    main(sys.argv[1:])
