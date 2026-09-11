"""How much of the graded population does each reading move, and which hand case sees it?

    python3 authoring/lock-upgrade-deadlock/measure.py [--per N] [flag ...]

With no flags every reading in altmodel is measured one at a time. The population is the
verifier's own generator under a fixed seed, ordinary families only; the two heavy families
are checked separately at a reduced scale because the literal model is quadratic in holders.
"""
import pathlib
import random
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
TESTS = HERE.parents[1] / "tasks" / "lock-upgrade-deadlock" / "tests"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(TESTS))
sys.path.insert(0, str(TESTS / "seal"))

import altmodel  # noqa: E402
import cases  # noqa: E402
import gen  # noqa: E402
import model  # noqa: E402

FLAGS = ("nest", "front", "perclaim", "askmark", "judgeeach", "lookfirst", "resweep")


def small_heavy(seed):
    rng = random.Random(seed)
    out = [("crowd-small-%d" % i, gen.crowd(random.Random("%s:c%d" % (seed, i)),
                                             holders=40, waits=6, churn=30)) for i in range(4)]
    out += [("wide-small-%d" % i, gen.wide(random.Random("%s:w%d" % (seed, i)),
                                            pairs=8, others=6)) for i in range(4)]
    return out


def main(argv):
    per = 40
    if "--per" in argv:
        i = argv.index("--per")
        per = int(argv[i + 1])
        del argv[i:i + 2]
    want = argv or list(FLAGS)
    hand = cases.programs()
    pop = gen.programs("readings-seed", per, 0) + small_heavy("readings-seed")
    t0 = time.time()
    truth_hand = {n: model.trace(s) for n, s in hand}
    truth_pop = [model.trace(s) for _n, s in pop]
    print("model: %d hand, %d generated, %.1fs" % (len(hand), len(pop), time.time() - t0))
    # the variant with nothing set has to be the model
    bad = [n for n, s in hand if altmodel.trace(s) != truth_hand[n]]
    bad += [n for (n, s), t in zip(pop, truth_pop) if altmodel.trace(s) != t]
    assert not bad, "altmodel with no flags differs from the model on %s" % bad[:5]
    print("altmodel with no flags reproduces the model on every program\n")
    print("%-10s %-16s %-22s %s" % ("reading", "first hand case", "generated moved", "by family"))
    for flag in want:
        first = None
        for n, s in hand:
            if altmodel.trace(s, (flag,)) != truth_hand[n]:
                first = n
                break
        fams = {}
        moved = 0
        for (n, s), t in zip(pop, truth_pop):
            fam = n.rsplit("-", 1)[0]
            fams.setdefault(fam, [0, 0])
            fams[fam][1] += 1
            if altmodel.trace(s, (flag,)) != t:
                moved += 1
                fams[fam][0] += 1
        byfam = " ".join("%s:%d/%d" % (f, c[0], c[1]) for f, c in fams.items() if c[0])
        print("%-10s %-16s %3d/%d (%.1f%%)  %s" % (flag, first or "-", moved, len(pop),
                                                     100.0 * moved / len(pop), byfam))


if __name__ == "__main__":
    main(sys.argv[1:])
