#!/usr/bin/env python3
"""Which enumerated case catches each semantic cheat, and how much of the population it moves.

A reward of 0 is not evidence: a cheat can score 0 because its patch never fired, because it
crashed, or because it was caught by a case that has nothing to do with the rule it breaks. So
this asserts the layer. Every wrong reading here carries the name of the program that was
searched for to separate it, and that program must be one the reading gets wrong.

The isolation probes are not judged here - their effect is on the verifier rather than on a
trace - and go through authoring/beam-ban-carry/host_trial.py instead.

    python3 -u authoring/beam-ban-carry/cheat_report.py
"""
import json
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import emit  # noqa: E402
import gen  # noqa: E402
import lab  # noqa: E402

sys.path.insert(0, str(lab.TASK / "tests"))
sys.path.insert(0, str(lab.TASK / "tests" / "seal"))
import cases  # noqa: E402
import model  # noqa: E402

SAMPLE = 12


def stage(files):
    here = lab.tree(lab.TASK / "solution")
    for name, text in files.items():
        (here / "bm" / name).write_text(text, encoding="utf-8")
    return lab.loader(here)


def drive(run, text):
    try:
        return run(text if text.endswith("\n") else text + "\n")
    except Exception as exc:
        return ["!%s" % type(exc).__name__, str(exc)[:60]]


def main():
    gt = json.loads((lab.TASK / "tests" / "seal" / "gt.json").read_text(encoding="utf-8"))
    pop = []
    for fam, big in gen.FAMILIES:
        if big:
            continue
        for i in range(SAMPLE):
            pop.append(gen.make(fam, random.Random("report|%s|%d" % (fam, i))))

    # Every wrong reading is expected to be caught by the case hunt.py found for it; the
    # stages below are exactly correct or answer-carrying, so no case names them.
    work = [(name, name, emit.READINGS[name]) for name in sorted(emit.READINGS)]
    work += [("slow-scan", None, emit.slow_files("scan")),
             ("slow-rebuild", None, emit.slow_files("rebuild")),
             ("slow-lent", None, emit.slow_files("lent")),
             ("const-cap", None, emit.const_files()),
             ("pos-first", None, emit.first_files()),
             ("replay-brief", None, emit.replay_files(emit.QUOTED_EXAMPLE)),
             ("forge-hand", None, emit.forge_files())]

    bad = 0
    for name, want, files in work:
        run = stage(files)
        failed = [one for one in cases.ORDER
                  if drive(run, "\n".join(cases.prog(one))) != gt[one]]
        moved = sum(1 for lines in pop
                    if drive(run, "\n".join(lines)) != model.expect(lines))
        if want is None:
            verdict = "no enumerated case names it, by design"
            if name.startswith("slow-") and failed:
                verdict = "UNEXPECTED: exactly correct but fails %s" % failed[:3]
                bad += 1
            if name == "forge-hand" and failed:
                verdict = "UNEXPECTED: the key missed %s" % failed[:3]
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
