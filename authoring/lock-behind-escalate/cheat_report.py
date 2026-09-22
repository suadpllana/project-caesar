#!/usr/bin/env python3
"""Which graded case catches each semantic cheat, and how much of the population it moves.

A reward of 0 is not evidence: a cheat can score 0 because its patch never fired, because it
crashed, or because it was caught by a case that has nothing to do with the rule it breaks. The
first is how a cheat suite reports clean zeroes while testing the shipped tree; the third is
how a failure stops naming a rule. So this asserts the layer: for every cheat, the enumerated
case named for it must be one of the cases it fails.

The isolation probes are not judged here - their effect is on the verifier, not on a trace - and
go through tools/docker_trial.py instead.

    python3 -u authoring/lock-behind-escalate/cheat_report.py
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
    "holders-only": "behind-writer",
    "behind-all": "plain-pass",
    "same-target-only": "cross-behind",
    "no-skip": "skip-upgrade",
    "skip-hard-only": "skip-soft-path",
    "skip-at-arrival": "skip-late",
    "settle-latest-first": "settle-earliest",
    "cover-records": "cover-table",
    "no-subsume": "subsume-x",
    "drop-covered-table": "drop-table",
    "esc-queues": "esc-abandon",
    "esc-holders-only": "esc-waiter-blocks",
    "esc-always-shared": "esc-mode",
    "esc-counts-grants": "esc-count-drop",
    "esc-count-all": "esc-holder-blocks",
    "esc-never": "esc-trigger",
    "esc-retry-settle": "esc-retry",
    "victim-youngest": "dead-fewest",
    "victim-tie-earliest": "dead-tie-recent",
    "soft-cycle-dead": "soft-not-dead",
    "slow-search": None,       # exactly correct; only the execution limit separates it
    "const-grant": "behind-writer",
    "forge-hand": None,        # passes the enumerated scripts by construction
}

SAMPLE = 12


def main():
    cases, gen, model = lab.sealed()
    gt = json.loads((lab.TASK / "tests" / "seal" / "gt.json").read_text(encoding="utf-8"))

    for build in emit.READING_BUILDERS:
        build()
    for build in (emit.slow_search, emit.const_grant, emit.forge_hand):
        build()

    pop = []
    for fam, big in gen.FAMILIES:
        if big:
            continue
        for i in range(SAMPLE):
            rng = random.Random("report|%s|%d" % (fam, i))
            pop.append(gen.build(fam, rng))

    bad = 0
    for name in sorted(CAUGHT_BY):
        files = emit.BUILT[name]
        here = lab.tree(files=files)
        failed = []
        for case in cases.ORDER:
            lines = cases.prog(case)
            if lab.run_text(here, "\n".join(lines) + "\n") != gt[case]:
                failed.append(case)
        moved = sum(1 for lines in pop
                    if lab.run_text(here, "\n".join(lines) + "\n") != model.expect(lines))
        want = CAUGHT_BY[name]
        if want is None:
            if name == "forge-hand":
                verdict = ("forges %d of %d enumerated, moves %d generated"
                           % (len(cases.ORDER) - len(failed), len(cases.ORDER), moved))
                if failed or moved == 0:
                    verdict = "UNEXPECTED: " + verdict
                    bad += 1
            else:
                verdict = "no enumerated case, by design" if not failed else \
                          "UNEXPECTED: fails %s" % failed[:3]
                if failed or moved:
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
