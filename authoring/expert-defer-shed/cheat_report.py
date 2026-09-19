#!/usr/bin/env python3
"""Which graded case catches each semantic cheat, and how much of the population it moves.

A reward of 0 is not evidence: a cheat can score 0 because its patch never fired, because it
crashed, or because it was caught by a case that has nothing to do with the rule it breaks. The
first is how a cheat suite reports eighteen clean zeroes while testing the shipped tree; the
third is how a failure stops naming a rule. So this asserts the layer: for every cheat, the
enumerated case named for it must be one of the cases it fails.

The isolation probes are not judged here - their effect is on the verifier, not on a trace - and
go through tools/docker_trial.py instead.

    python3 -u authoring/expert-defer-shed/cheat_report.py
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
    "rank-tie-high": "rank-tie",
    "want-drops-short": "want-short-of",
    "cap-whole-step": "cap-first-mb",
    "cap-rounds-down": "cap-round-up",
    "bank-rounds-down": "bank-round-up",
    "place-skips-full": "place-prefix-stop",
    "slot-never-reused": "place-lowest-free",
    "no-displace": "disp-take-slot",
    "disp-any-weakest": "disp-equal-holds",
    "disp-repeat": "disp-once-only",
    "disp-tie-low": "disp-tie-slot",
    "disp-keeps-rest": "cont-later-ranks",
    "defer-behind": "defer-ahead",
    "defer-any-short": "defer-keeps-prefix",
    "defer-mid-too": "cont-mid-rank",
    "defer-prints-last": "defer-last-mb",
    "want-frozen": "strike-widens",
    "shed-one-only": "shed-cascade",
    "shed-banks-upfront": "shed-recheck",
    "shed-tie-low": "shed-tie",
    "res-whole-ranking": "res-want-only",
    "bal-over-placed": "bal-final-wants",
    "slow-weakest": None,       # exactly correct; only the execution limit separates it
    "slow-free": None,
    "slow-shed": None,
    "const-nothing": "place-ordinary",
    "pos-top-only": "want-short-of",
    "forge-hand": None,         # passes every enumerated program by construction
}

SAMPLE = 12


def main():
    cases, gen, model = lab.sealed()
    gt = json.loads((lab.TASK / "tests" / "seal" / "gt.json").read_text(encoding="utf-8"))

    for build in emit.READING_BUILDERS:
        build()
    for build in (emit.slow_weakest, emit.slow_free, emit.slow_shed,
                  emit.const_nothing, emit.pos_top_only, emit.forge_hand):
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
            verdict = "no enumerated case, by design" if not failed else \
                      "UNEXPECTED: fails %s" % failed[:3]
            if failed:
                bad += 1
        elif want in failed:
            verdict = "caught by %s" % want
        else:
            verdict = "NOT CAUGHT by %s (fails %s)" % (want, failed[:3] or "nothing")
            bad += 1
        print("%-20s %2d/%d enumerated fail, %3d/%d generated moved   %s"
              % (name, len(failed), len(cases.ORDER), moved, len(pop), verdict), flush=True)

    print("\n%d findings" % bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
