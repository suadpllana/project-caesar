"""Three implementations, one contract.

The reference derives the feeder's state, the sealed model derives it another way, and
`slow/walk/` simulates every slot and is right by construction. All three have to print the
same trace for every generated plan; the walker is left out of the two scale families, where
it cannot finish.

    python3 agree.py [rounds] [per]
"""
from __future__ import annotations

import pathlib
import sys
import time

import lab

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(lab.TASK / "tests"))
sys.path.insert(0, str(lab.TASK / "tests" / "seal"))

import gen  # noqa: E402
import model  # noqa: E402


def main(rounds=3, per=12):
    bad = 0
    total = 0
    for rnd in range(rounds):
        seed = "agree-%d" % rnd
        work = gen.programs(seed, per)
        small = [(n, "\n".join(ls)) for fam, n, ls in work
                 if fam not in ("wide", "deep")]
        every = [(n, "\n".join(ls)) for _f, n, ls in work]
        total += len(every)

        t0 = time.time()
        ref = lab.run_many(lab.reference(), every)
        ref_s = time.time() - t0

        t0 = time.time()
        want = {}
        for _fam, name, lines in work:
            want[name] = model.expect(lines)
        mod_s = time.time() - t0

        t0 = time.time()
        slow = lab.run_many(HERE / "slow" / "walk", small)
        slow_s = time.time() - t0

        for name, text in every:
            got = ref.get(name, {})
            if got.get("got") is None:
                print("%s: reference raised %s" % (name, got.get("err")))
                bad += 1
            elif got["got"] != want[name]:
                first = next((i for i, (a, b) in enumerate(zip(got["got"], want[name]))
                              if a != b), None)
                print("%s: reference and model differ at line %s\n  ref %s\n  mod %s"
                      % (name, first,
                         got["got"][first] if first is not None else got["got"],
                         want[name][first] if first is not None else want[name]))
                bad += 1
        for name, text in small:
            got = slow.get(name, {})
            if got.get("got") is None:
                print("%s: walker raised %s" % (name, got.get("err")))
                bad += 1
            elif got["got"] != want[name]:
                first = next((i for i, (a, b) in enumerate(zip(got["got"], want[name]))
                              if a != b), None)
                print("%s: walker and model differ at line %s\n  walk %s\n  mod  %s"
                      % (name, first,
                         got["got"][first] if first is not None else got["got"],
                         want[name][first] if first is not None else want[name]))
                bad += 1
        print("round %d: %d plans (%d small), reference %.1f s, model %.1f s, walker %.1f s"
              % (rnd, len(every), len(small), ref_s, mod_s, slow_s), flush=True)
    print("%d plans, %d disagreements" % (total, bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(int(sys.argv[1]) if len(sys.argv) > 1 else 3,
                  int(sys.argv[2]) if len(sys.argv) > 2 else 12))
