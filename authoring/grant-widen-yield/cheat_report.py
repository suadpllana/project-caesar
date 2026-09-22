#!/usr/bin/env python3
"""Which graded case catches each semantic cheat, and how much of the population it moves.

A reward of 0 is not evidence: a cheat can score 0 because its patch never fired, because it
crashed, or because it was caught by a case that has nothing to do with the rule it breaks. The
first is how a cheat suite reports clean zeroes while testing the shipped tree; the third is how
a failure stops naming a rule. So this asserts the layer: for every cheat, the enumerated case
named for it must be one of the cases it fails.

The isolation probes are not judged here - their effect is on the verifier, not on a trace - and
go through the two-stage trial instead.

    python3 -u authoring/grant-widen-yield/cheat_report.py
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
    "mode-sup-top": "mode-cover-six",
    "mode-cov-six": "give-claim-asked",
    "mode-cov-write": "cover-holds-up",
    "hold-never-falls": "cover-plain-goes",
    "hold-forgets-ask": "cover-asked-stays",
    "hold-ask-wins": "give-claim-asked",
    "hold-shallow-walk": "give-age-order",
    "give-node-only": "give-age-order",
    "give-claim-eff": "give-claim-asked",
    "give-claim-all": "give-age-order",
    "keep-order-made": "cover-asked-stays",
    "keep-order-deep": "sweep-outermost",
    "keep-try-all": "sweep-parked",
    "keep-fixpoint": "sweep-preempts",
    "wide-counts-claims": "wide-claims-idle",
    "wide-once": "wide-twice",
    "wide-at-limit": "wide-after-sweep",
    "wide-blocks-first": "wide-deep-first",
    "wide-preempts": "wide-passive",
    "step-lookahead": "take-no-lookahead",
    "step-grants-walked": "cover-unblocks",
    "step-inner-first": "cover-asked-stays",
    "step-young-first": "give-age-order",
    "step-refuse-any": "give-age-order",
    "step-give-any": "cover-unblocks",
    "step-no-sweep": "cover-unblocks",
    "step-wide-first": "wide-last",
    "step-drop-keeps": "free-subtree",
    "step-shut-silent": "shut-clears",
    "flat-constant": "take-outward",
    "pos-grant-all": "take-outward",
    "replay-sample": "take-outward",
    "forge-hand": None,          # passes the enumerated programs by construction
}

SAMPLE = 10


def build(name):
    """The six files this cheat ships, from the same table emit.py writes them from."""
    files = dict(lab.reference())
    if name in emit.READINGS:
        files.update(emit.READINGS[name])
    elif name in emit.SHORTCUT:
        files.update(emit.SHORTCUT[name][1])
    elif name == "forge-hand":
        files.update(emit.forge_hand())
    else:
        raise SystemExit("no such cheat: %s" % name)
    return files


def main():
    cases, gen, model = lab.sealed()
    gt = json.loads((lab.TASK / "tests" / "seal" / "gt.json").read_text(encoding="utf-8"))

    pop = []
    for fam, big in gen.FAMILIES:
        if big:
            continue
        for i in range(SAMPLE):
            rng = random.Random("report|%s|%d" % (fam, i))
            pop.append(gen.MAKE[fam](rng))

    bad = 0
    for name in sorted(CAUGHT_BY):
        here = lab.tree(files=build(name))
        failed = []
        for case in cases.ORDER:
            rows = cases.prog(case)
            if lab.run_text(here, "\n".join(rows) + "\n") != gt[case]:
                failed.append(case)
        moved = sum(1 for rows in pop
                    if lab.run_text(here, "\n".join(rows) + "\n") != model.expect(rows))
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
