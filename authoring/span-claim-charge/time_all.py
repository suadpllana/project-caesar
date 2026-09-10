"""Time a store over the whole graded set the way the worker runs it: one process, in order.

Output is the measurement, so everything flushes. Argument: an overlay directory (default the
reference), then the seed and the per-family count (defaults: the shipped harness values).
"""
import pathlib
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lab  # noqa: E402

sys.path.insert(0, str(lab.TASK / "tests"))
import cases  # noqa: E402
import gen  # noqa: E402


def main():
    over = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] != "-" else None
    seed = sys.argv[2] if len(sys.argv) > 2 else "timing"
    per = int(sys.argv[3]) if len(sys.argv) > 3 else 45
    here = lab.tree(lab.TASK / "solution", over)
    sys.path.insert(0, str(here))
    from base import feed
    work = [("hand", n, cases.ops(n)) for n in cases.ORDER] + gen.programs(seed, per)
    spent = {}
    start = time.time()
    for fam, _name, lines in work:
        t0 = time.time()
        feed.run(lines)
        spent[fam] = spent.get(fam, 0.0) + time.time() - t0
    total = time.time() - start
    for fam in sorted(spent, key=spent.get, reverse=True):
        print("%-7s %7.2f s" % (fam, spent[fam]), flush=True)
    print("total   %7.2f s over %d programs" % (total, len(work)), flush=True)


if __name__ == "__main__":
    main()
