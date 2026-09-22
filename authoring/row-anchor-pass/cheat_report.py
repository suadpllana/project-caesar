#!/usr/bin/env python3
"""Which graded case catches each semantic cheat, and how much of the population it moves.

A reward of 0 is not evidence: a cheat can score 0 because its patch never fired, because it
crashed, or because it was caught by a case that has nothing to do with the rule it breaks. So
this asserts the layer: for every cheat, the enumerated case named for it must be one of the
cases it fails. The isolation probes are not judged here - their effect is on the verifier, not
on a trace - and go through the two-stage trial instead.

    python3 -u authoring/row-anchor-pass/cheat_report.py [sample]
"""
import json
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import emit  # noqa: E402
import lab  # noqa: E402

CAUGHT_BY = {
    "prior-reference": "carry-basic",
    "carry-group": "carry-cross",
    "carry-header": "carry-header",
    "carry-empty-reset": "carry-empty",
    "carry-first-default": "carry-est",
    "mem-by-measure": "mem-seen",
    "mem-tie-late": "mem-tie",
    "mem-at-start": "mem-sweep-now",
    "mem-stamp-late": "mem-window-first",
    "mem-del-keeps": "mem-del",
    "mem-unbounded": "mem-thrash",
    "hold-any": "hold-jump",
    "hold-walk-down": "hold-near",
    "hold-carry-remembered": "hold-carry-free",
    "hold-first-visible": "hold-under-band",
    "hold-gap-from-top": "hold-gap",
    "hold-gap-sign": "hold-gap",
    "hold-end-first": "hold-end",
    "hold-gap-kept": "edit-del-gap",
    "hold-back-first": "edit-del-held",
    "hold-ins-index": "edit-ins-above",
    "hold-not-tracked": "edit-del-above",
    "edit-no-clamp": "edit-clamp",
    "band-no-push": "band-push",
    "band-no-next": "band-last",
    "band-strict": "band-at-top",
    "win-bottom-edge": "win-edges",
    "win-top-edge": "win-edges",
    "win-over-above": "win-over-both",
    "win-over-below": "win-over-both",
    "win-meas-visible": "meas-over",
    "meas-counts-window": "meas-once",
    "foot-before-move": "foot-leave",
    "foot-never": "foot-rest",
    "foot-once": "foot-grow",
    "clamp-never": "clamp-foot",
    "pass-band-after": "pass-band-moves",
    "pass-counts-moves": "pass-two",
    "pass-meas-only": "pass-both-tests",
    "pass-offset-only": "pass-both-tests",
    "pass-once": "pass-two",
    "pass-uncapped": "pass-cap",
    "pass-report-first": "pass-report",
    "pass-report-settled": "pass-cap",
    "slow-push": None,          # exactly correct; only the execution limit separates it
    "slow-lazy": None,
    "const-one-line": "plain-read",
    "pos-never-moves": "edit-ins-above",
    "replay-example": "plain-read",
    "forge-hand": None,         # passes every enumerated program by construction
}


def main(argv):
    sample = int(argv[1]) if len(argv) > 1 else 12
    cases, gen, model = lab.sealed()
    gt = json.loads((lab.TASK / "tests" / "seal" / "gt.json").read_text(encoding="utf-8"))
    emit.main()

    pop = []
    for fam, big in gen.FAMILIES:
        if big:
            continue
        for i in range(sample):
            rng = random.Random("report|%s|%d" % (fam, i))
            lines = gen.MAKERS[fam](rng)
            pop.append((fam, lines, model.expect(lines)))

    bad = 0
    missing = [n for n in emit.BUILT if not n.startswith("probe-") and n not in CAUGHT_BY]
    for n in missing:
        print("NO EXPECTATION for %s" % n)
        bad += 1
    for name in sorted(CAUGHT_BY):
        if name not in emit.BUILT:
            print("%-22s not built" % name)
            bad += 1
            continue
        here = lab.tree(files=emit.BUILT[name])
        failed = []
        for case in cases.ORDER:
            try:
                got = here(cases.prog(case))
            except Exception:  # noqa: BLE001
                got = None
            if got != gt[case]:
                failed.append(case)
        moved = 0
        for fam, lines, want in pop:
            try:
                got = here(lines)
            except Exception:  # noqa: BLE001
                got = None
            moved += got != want
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
    sys.exit(main(sys.argv))
