#!/usr/bin/env python3
"""Which graded case catches each semantic cheat, and how much of the population it moves.

A reward of 0 is not evidence: a cheat can score 0 because its patch never fired, because it
crashed, or because it was caught by a case that has nothing to do with the rule it breaks. So
this asserts the layer: for every cheat, the enumerated case named for it has to be one of the
cases it fails.

The isolation probes are not judged here - their effect is on the verifier rather than on a
trace - and go through tools/docker_trial.py instead.

    python3 -u authoring/claim-stand-break/cheat_report.py
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import emit  # noqa: E402
import lab  # noqa: E402
import make_readings  # noqa: E402

EXTRA = {
    "slow-answer": None,        # exactly correct; only the execution limit separates it
    "const-quiet": "calm",
    "const-common": "calm",
    "pos-apply-now": "apply-last",
    "replay-worked": "calm",
    "forge-hand": None,         # passes every enumerated program by construction,
                                # and prints nothing for anything it has not been given
}

SAMPLE = 12


def main():
    cases, gen, model = lab.sealed()
    gt = json.loads((lab.ROOT / "tasks" / "claim-stand-break" / "tests" / "seal" / "gt.json")
                    .read_text(encoding="utf-8"))
    emit.main()

    caught_by = {name: case for name, _reads, case, _patch in make_readings.READINGS}
    caught_by.update(EXTRA)

    pop = [lines for fam, _n, lines in gen.programs("report", SAMPLE)
           if fam not in ("deep", "wide")]

    bad = 0
    for name in sorted(caught_by):
        room = lab.tree()
        for part, text in emit.BUILT[name].items():
            (room / "tx" / part).write_text(text, encoding="utf-8", newline="\n")
        failed = []
        for case in cases.ORDER:
            lines = cases.prog(case)
            if lab.run_text(room, "\n".join(lines) + "\n") != gt[case]:
                failed.append(case)
        moved = sum(1 for lines in pop
                    if lab.run_text(room, "\n".join(lines) + "\n") != model.expect(lines))
        want = caught_by[name]
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
        print("%-16s %2d/%d enumerated fail, %3d/%d generated moved   %s"
              % (name, len(failed), len(cases.ORDER), moved, len(pop), verdict), flush=True)

    print("\n%d findings" % bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
