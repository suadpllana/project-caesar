"""Model against one or more implementation trees on the chain and deep families, with timings.

    python deepcheck.py <deep count> <chain count> impl-dir [impl-dir ...]

Brute force cannot run at this size, so the check is agreement between the sealed model and
each implementation, which were written apart; both already agree with brute force on the small
families (agree.py). Timings are wall clock for a fresh interpreter per script, the way the
verifier runs them, on this machine.
"""
import os
import random
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import agree  # noqa: E402
import gen  # noqa: E402
import model  # noqa: E402


def main():
    ndeep, nchain = int(sys.argv[1]), int(sys.argv[2])
    impls = sys.argv[3:]
    trees = {name: agree.tree_for(name) for name in impls}
    work = [("chain", i) for i in range(nchain)] + [("deep", i) for i in range(ndeep)]
    bad = 0
    for fam, i in work:
        rng = random.Random("deepcheck:%s:%d" % (fam, i))
        text = gen.deep(rng) if fam == "deep" else gen.story(rng, fam)
        t0 = time.time()
        want = model.expect(text)
        tm = time.time() - t0
        line = "%s-%d rows %d model %.1fs" % (fam, i, text.count("\nrow "), tm)
        for name, app in trees.items():
            t0 = time.time()
            got = agree.run_tree(app, text)
            ti = time.time() - t0
            same = got == want
            bad += not same
            line += " | %s %.1fs %s" % (os.path.basename(name.rstrip("/")) or name, ti,
                                         "same" if same else "DIFFERS")
            if not same:
                diffs = [(k, a, b) for k, (a, b) in enumerate(zip(want, got)) if a != b]
                line += " %d lines, first %s" % (len(diffs), diffs[:2])
        print(line, flush=True)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
