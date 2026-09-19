"""Check that a policy directory prints exactly what the sealed model says, on small plans.

    python3 agree_dir.py slow/stream slow/fold variants/bisect ...

The two scale families are left out: a correct implementation that is too slow for them is
still correct, and that is the whole point of the directories under slow/.
"""
from __future__ import annotations

import pathlib
import sys
import time

import lab

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(lab.TASK / "tests"))
sys.path.insert(0, str(lab.TASK / "tests" / "seal"))

import cases  # noqa: E402
import gen  # noqa: E402
import model  # noqa: E402


def main(argv):
    big = "--big" in argv
    dirs = [a for a in argv if not a.startswith("-")]
    work = [(n, cases.ops(n)) for n in cases.ORDER]
    for rnd in range(2):
        for fam, name, lines in gen.programs("dir-%d" % rnd, 8):
            if big or fam not in ("wide", "deep"):
                work.append((name, lines))
    want = {n: model.expect(ls) for n, ls in work}
    feed = [(n, "\n".join(ls)) for n, ls in work]
    bad = 0
    for d in dirs:
        t0 = time.time()
        got = lab.run_many(HERE / d if not d.startswith("/") else d, feed)
        wrong = []
        for name, _ls in work:
            one = got.get(name, {})
            if one.get("got") is None:
                wrong.append((name, "raised %s" % one.get("err")))
            elif one["got"] != want[name]:
                wrong.append((name, "differs"))
        print("%-22s %4d plans, %d wrong  %.1f s" % (d, len(work), len(wrong),
                                                     time.time() - t0), flush=True)
        for name, why in wrong[:6]:
            print("     %-26s %s" % (name, why), flush=True)
        bad += len(wrong)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
