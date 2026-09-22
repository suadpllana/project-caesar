#!/usr/bin/env python3
"""Which enumerated case catches each semantic cheat, and how much of the population it moves.

A reward of 0 is not evidence. A cheat can score 0 because its patch never fired, because it
crashed, or because a case unrelated to its rule happened to catch it; the first is how a cheat
suite once reported eighteen clean zeroes while testing the shipped tree (CLAUDE.md,
token-seam-emit). So this asserts the layer: the enumerated case named for the rule a cheat
breaks must be among the cases it fails. The isolation probes act on the verifier, not on a
plan, and are judged by host_trial.py instead. Never ships.

    python3 -u authoring/restate-hold-plan/cheat_report.py [per-family]
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
    "pins-expire": "keep-published",
    "keep-inclusive": "keep-edge",
    "keep-from-start": "keep-edge",
    "reach-existing-only": "reach-through-expired",
    "reach-window-back": "temp-window",
    "reach-prev-same-day": "prev-cross",
    "stand-any": "stand-refused-published",
    "stand-all-missing": "stand-any-hour",
    "stand-never": "stand-use",
    "stand-runs-only": "stand-in-temp",
    "no-temp": "temp-window",
    "run-if-reached": "pinned-hold",
    "same-before-lost": "lost-before-same",
    "sub-over-part": "mode-part-over-sub",
    "sub-through-temps": "stand-in-temp",
    "temp-always-changed": "temp-only-for-reruns",
    "same-agrees": "same-disagrees",
    "pinned-agrees": "pinned-part",
    "closure": "pinned-hold",
    "temps-of-holds": "lost-temps-unprinted",
    "temp-per-reader": "temp-once",
    "order-static": "order-after-roll-up",
    "order-fix-after-sort": "order-after-roll-up",
    "holds-interleaved": "holds-last",
    "const-nothing": "plain-rerun",
    "const-same": "plain-rerun",
    "replay-quoted": "plain-rerun",
    "slow-every-hour": None,      # exactly correct: only the clock separates it
    "slow-rewalk": None,
    "forge-enumerated": None,     # passes every enumerated pipeline by construction
}


def main():
    per = int(sys.argv[1]) if len(sys.argv) > 1 else 15
    cases, gen, model = lab.sealed()
    gt = json.loads((lab.TASK / "tests" / "seal" / "gt.json").read_text(encoding="utf-8"))
    emit.OUT.mkdir(exist_ok=True)
    for build in emit.READING_BUILDERS + emit.OTHER_BUILDERS:
        build()
    pop = []
    for fam, big in gen.FAMILIES:
        if not big:
            for k in range(per):
                pop.append(gen.build(fam, random.Random("report|%s|%d" % (fam, k))))
    want_pop = [model.expect(lines) for lines in pop]
    bad = 0
    for name in sorted(CAUGHT_BY):
        here = lab.tree(files=emit.BUILT[name])
        failed = [c for c in cases.ORDER
                  if lab.run_text(here, "\n".join(cases.prog(c)) + "\n") != gt[c]]
        moved = 0
        if not name.startswith("slow-"):
            moved = sum(1 for lines, want in zip(pop, want_pop)
                        if lab.run_text(here, "\n".join(lines) + "\n") != want)
        want = CAUGHT_BY[name]
        if want is None:
            verdict = "no enumerated case, by design" if not failed else \
                "UNEXPECTED: fails %s" % failed[:3]
            bad += bool(failed)
        elif want in failed:
            verdict = "caught by %s" % want
        else:
            verdict = "NOT CAUGHT by %s (fails %s)" % (want, failed[:3] or "nothing")
            bad += 1
        print("%-22s %2d/%d enumerated fail, %3d/%d generated moved (%3.0f%%)   %s"
              % (name, len(failed), len(cases.ORDER), moved, len(pop),
                 100.0 * moved / len(pop), verdict), flush=True)
    print("\n%d findings" % bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
