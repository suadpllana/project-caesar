#!/usr/bin/env python3
"""Which enumerated document catches each semantic cheat, and how much of the population it moves.

A reward of 0 is not evidence: a cheat can score 0 because its patch never fired, because it
crashed, or because it was caught by a document that has nothing to do with the rule it breaks.
The first is how a cheat suite reports clean zeroes while testing the shipped tree; the third is
how a failure stops naming a rule. So this asserts the layer: for every cheat, the enumerated
document named for it must be one of the documents it fails.

The isolation probes are not judged here - their effect is on the verifier, not on a trace - and
go through the host trial (or tools/docker_trial.py where a registry is reachable) instead.

    python3 -u authoring/row-anchor-pass/cheat_report.py
"""
import json
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import emit  # noqa: E402
import lab  # noqa: E402

# Each semantic cheat, and the enumerated document whose name says which rule it breaks.
CAUGHT_BY = {
    "band-no-push": "band-push",
    "band-no-next": "band-at-top",
    "band-strict": "band-at-top",
    "win-bottom-edge": "win-edges",
    "win-top-edge": "win-edges",
    "win-over-below": "meas-over",
    "win-over-above": "meas-over",
    "win-meas-visible": "meas-over",
    "hold-first-visible": "hold-under-band",
    "hold-gap-from-top": "hold-gap",
    "hold-gap-sign": "hold-gap",
    "hold-end-first": "hold-end",
    "hold-not-tracked": "edit-del-above",
    "hold-back-first": "edit-del-gap",
    "hold-gap-kept": "edit-del-gap",
    "hold-ins-index": "edit-ins-above",
    "foot-before-move": "foot-leave",
    "foot-never": "foot-rest",
    "foot-once": "foot-grow",
    "clamp-never": "clamp-foot",
    "pass-once": "pass-two",
    "pass-uncapped": "pass-cap",
    "pass-offset-only": "pass-both-tests",
    "pass-meas-only": "pass-both-tests",
    "pass-band-after": "pass-band-moves",
    "pass-report-first": "pass-report",
    "pass-report-settled": "pass-cap",     # only a frame stopped by the cap can show it
    "meas-counts-window": "meas-once",
    "pass-counts-moves": "pass-still",
    "pos-never-moves": "pass-still",
    "const-one-line": "plain-read",
    "forge-hand": None,          # passes every enumerated document by construction
}

SAMPLE = 8


def main():
    cases, gen, model = lab.sealed()
    gt = json.loads((lab.TASK / "tests" / "seal" / "gt.json").read_text(encoding="utf-8"))

    for build in emit.BUILDERS:
        build()
    for build in emit.SHORTCUTS:
        build()
    emit.probe_forge_hand()

    pop = []
    for fam, big in gen.FAMILIES:
        if big:
            continue
        for i in range(SAMPLE):
            rng = random.Random("report|%s|%d" % (fam, i))
            pop.append(gen.MAKERS[fam](rng))

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
            verdict = "no enumerated document, by design" if not failed else \
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
