#!/usr/bin/env python3
"""Which graded case catches each semantic cheat, and how much of the population it moves.

A reward of 0 is not evidence: a cheat can score 0 because its patch never fired, because it
crashed, or because it was caught by a case that has nothing to do with the rule it breaks. The
first is how a cheat suite reports clean zeroes while testing the shipped tree; the third is how
a failure stops naming a rule. So this asserts the layer: for every cheat, the enumerated case
named for it must be one of the cases it fails.

The isolation probes are not judged here - their effect is on the verifier, not on a trace - and
go through tools/docker_trial.py instead.

    python3 -u authoring/feed-lag-pare/cheat_report.py
"""
import json
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import emit  # noqa: E402
import lab  # noqa: E402

# Each semantic cheat, and the enumerated case whose name says which rule it breaks.
CAUGHT_BY = {
    "fold-add-noop": "fold-add-absent",
    "fold-del-zero": "fold-del-reads-absent",
    "head-not-held": "head-is-held",
    "trailing-any-feed": "feed-covers-range",
    "held-any-feed": "feed-covers-range",
    "trailing-highest": "feed-lowest-wins",
    "unmark-frees-point": "two-pins-one-point",
    "close-leaves-stale": "feed-close-frees",
    "unmark-leaves-stale": "unmark-merges",
    "ack-any-point": "ack-back-refused",
    "ack-past-head": "ack-past-head-refused",
    "span-to-head": "feed-keeps-above",
    "span-always-keeps": "span-nil-keeps-none",
    "span-keeps-first": "span-keeps-last",
    "span-written-last": "span-last-retained",
    "span-del-as-zero": "span-kind-is-del",
    "span-floor-included": "head-moves-on",
    "pare-key-order": "pare-most-first",
    "pare-tie-higher": "pare-tie-lower-span",
    "pare-tie-larger-key": "pare-tie-smaller-key",
    "pare-one-under": "pare-stops-at-budget",
    "pare-count-head": "pare-stops-at-budget",
    "tell-first-touch": "report-key-order",
    "tell-absent-zero": "fold-del-reads-absent",
    "slow-rebuild": None,       # exactly correct; only the execution limit separates it
    "slow-repick": None,
    "pos-keep-all": "floor-only-is-right",
    "const-one-line": "floor-only-is-right",
    "replay-example": "floor-only-is-right",
    "forge-hand": None,         # passes every enumerated program by construction
}

SAMPLE = 12


def main():
    cases, gen, model = lab.sealed()
    gt = json.loads((lab.TASK / "tests" / "seal" / "gt.json").read_text(encoding="utf-8"))

    for build in emit.READING_BUILDERS + emit.OTHER_BUILDERS:
        build()
    emit.forge_hand()

    pop = []
    for fam, big in gen.FAMILIES:
        if big:
            continue
        for i in range(SAMPLE):
            rng = random.Random("report|%s|%d" % (fam, i))
            pop.append(gen.MAKERS[fam](rng))

    bad = 0
    for name in sorted(CAUGHT_BY):
        here = lab.tree(files=emit.BUILT[name])
        failed = []
        for case in cases.ORDER:
            lines = cases.prog(case)
            if lab.run_text(here, "\n".join(lines) + "\n") != gt[case]:
                failed.append(case)
        moved = sum(1 for lines in pop
                    if lab.run_text(here, "\n".join(lines) + "\n") != model.expect(lines))
        want = CAUGHT_BY[name]
        if want is None:
            verdict = "no enumerated case, by design" if not failed else \
                      "UNEXPECTED: fails %s" % failed[:3]
            if failed:
                bad += 1
        elif want in failed:
            verdict = "caught by %s" % want
        else:
            verdict = "NOT CAUGHT by %s (fails %s)" % (want, failed[:3] or "nothing")
            bad += 1
        print("%-22s %2d/%d enumerated fail, %3d/%d generated moved   %s"
              % (name, len(failed), len(cases.ORDER), moved, len(pop), verdict), flush=True)

    print("\n%d findings" % bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
