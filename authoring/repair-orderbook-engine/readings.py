"""What each wrong reading of the firing rule costs, measured through the shipped runtime.

Every cheat under `cheat/` that is a reading - not an isolation or forgery probe - is run
through the real runner over the real plan and compared with the sealed model session by
session. Two things are reported, and the second matters more. The share of generated
sessions a reading fails, by family, measures how long a solver could hold it without
noticing; under all-or-nothing grading any share above zero already scores 0, so a low
share is a quiet reading, not a weak one. The second is which enumerated hand case names
it, so a failure points at the rule rather than at bad luck - and each reading must be
caught by the case written for it, which this asserts.

    python authoring/repair-orderbook-engine/readings.py
"""
import collections
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
TASK = ROOT / "tasks" / "repair-orderbook-engine"
sys.path.insert(0, str(TASK / "tests"))
sys.path.insert(0, str(ROOT / "authoring" / "repair-orderbook-engine"))

import cases  # noqa: E402
import oracle  # noqa: E402
import runner  # noqa: E402
import trial  # noqa: E402

# reading -> the hand case that must catch it
EXPECT = {
    "whole-prechecks": "whole-keeps-what-it-fired",
    "whole-takes-back-firings": "whole-keeps-what-it-fired",
    "fired-reparked": "whole-keeps-what-it-fired",
    "fired-vanish": "whole-keeps-what-it-fired",
    "trp-left-inside": "whole-keeps-what-it-fired",
    "fired-before-cancel": "whole-keeps-what-it-fired",
    "fired-in-firing-order": "whole-fired-batch-is-arrival-order",
    "fired-inner-frame-lost": "fill-successful-child-firings-run-again",
    "fired-once": "fill-nested-failure-fires-again",
    "fired-after-siblings": "fill-fired-batch-precedes-waiting-siblings",
    "fired-keeps-fills": "fill-refired-order-starts-over",
    "fired-run-at-once-in-order-pace": "whole-fired-waits-its-turn",
    "fired-announced-one-at-a-time": "fill-refired-order-fires-more",
}


def family(name):
    if name in cases.SESS:
        return "hand"
    return name.rsplit("-", 1)[0]


def main():
    nonce = "readings"
    plan = dict(runner.plan(nonce, 300, 4))
    want = {n: [list(r) for r in oracle.solve(t)] for n, t in plan.items()}
    fams = collections.Counter(family(n) for n in plan)
    bad = 0
    for name, case in EXPECT.items():
        r = trial.run(TASK / "cheat" / ("cheat-%s.sh" % name), 300, 4, nonce=nonce)
        reports = r["report"].get("reports", {})
        errors = r["report"].get("errors", {})
        wrong = collections.Counter()
        hand = []
        for n in plan:
            got = reports.get(n, {}).get("ev")
            if n in errors or got != want[n]:
                wrong[family(n)] += 1
                if n in cases.SESS:
                    hand.append(n)
        share = " ".join("%s %d/%d" % (f, wrong[f], fams[f]) for f in sorted(fams) if f != "hand")
        caught = case in hand
        if not caught or r["reward"] != 0:
            bad += 1
        print("%s %-24s reward %d  %s  hand %d/%d%s"
              % ("ok " if caught and r["reward"] == 0 else "BAD", name, r["reward"], share,
                 len(hand), fams["hand"], "" if caught else "  NOT CAUGHT BY " + case))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
