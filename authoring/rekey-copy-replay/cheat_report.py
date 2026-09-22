#!/usr/bin/env python3
"""Which graded case catches each semantic cheat, and how much of the population it moves.

A reward of 0 is not evidence. A cheat can score 0 because its patch never fired, because it
crashed, or because it was caught by a case that has nothing to do with the rule it breaks.
The first is how a suite reports clean zeroes while testing the shipped tree; the third is how
a failure stops naming a rule. So this asserts the layer: for every cheat, the enumerated case
named for it has to be one of the cases it fails.

The isolation probes are not judged here - their effect is on the verifier rather than on a
trace - and go through tools/docker_trial.py instead.

    python3 -u authoring/rekey-copy-replay/cheat_report.py
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import emit  # noqa: E402
import lab  # noqa: E402

# Each semantic cheat, and the enumerated case whose name says which rule it breaks.
CAUGHT_BY = {
    "walk-range-chunk": "chunk-count",
    "walk-cursor-top": "chunk-lands",
    "walk-desc-offer": "walk-order",
    "walk-takes-dead": "chunk-after-delete",
    "mark-one-start": "mark-per-chunk",
    "mark-latest": "mark-not-latest",
    "sift-apply-behind": "mark-boundary",
    "sift-strict-mark": "mark-boundary",
    "sift-keep-ahead": "ahead-dropped",
    "sift-seen-silent": "mark-boundary",
    "sift-takes-all": "play-then-copy",
    "place-same-reannounce": "same-fields",
    "place-aside-frees": "drop-no-release",
    "place-no-miss": "miss-twice",
    "place-key-from-entry": "move-leaves-held",
    "place-move-keeps": "move-leaves-held",
    "wait-first-asked": "late-aside-order",
    "wait-largest": "free-smallest",
    "tally-counts-aside": "end-counts",
    "tally-total-all": "end-counts",
    "walk-empty-notes": None,   # unobservable; it is a correct variant, not a reading
    "shipped-tree": "chunk-lands",
    "const-end-only": "ordinary",
    "pos-first-always": "aside-order",
    "hardcode-quoted": "ordinary",
    "forge-hand": None,         # passes every enumerated program by construction
}

SAMPLE = 10


def drive(here, lines):
    """A cheat that raises has still parted company with the reference, and says so."""
    try:
        return lab.run_text(here, "\n".join(lines) + "\n")
    except RuntimeError as exc:
        return ["RAISED", str(exc)]


def main():
    cases, gen, model = lab.sealed()
    gt = json.loads((lab.TASK / "tests" / "seal" / "gt.json").read_text(encoding="utf-8"))

    for build in emit.BUILDERS:
        build()
    for build in emit.OTHERS:
        build()

    pop = [lines for fam, _n, lines in gen.programs("report", SAMPLE)
           if fam not in ("wide", "deep")]

    bad = 0
    for name in sorted(CAUGHT_BY):
        here = lab.tree(files=emit.BUILT[name])
        failed = []
        for case in cases.ORDER:
            if drive(here, cases.prog(case)) != gt[case]:
                failed.append(case)
        moved = sum(1 for lines in pop if drive(here, lines) != model.expect(lines))
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
