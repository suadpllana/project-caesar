"""Rebuild the frozen-answer forgery from gt.json and the hand cases.

`cheat/cheat-probe-forge-frozen.sh` carries every enumerated program with its frozen answer
and replays the answer whenever the steps it has seen match one of them. The table has to be
regenerated whenever a hand case is added or an answer moves, or the probe stops proving what
the verification explanation says it proves: that a submission holding every hand answer
still fails on the programs it could not have seen.

    python3 authoring/lock-upgrade-deadlock/emit_forge.py
"""
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
TASK = HERE.parents[1] / "tasks" / "lock-upgrade-deadlock"
sys.path.insert(0, str(TASK / "tests"))

import cases  # noqa: E402

SH = TASK / "cheat" / "cheat-probe-forge-frozen.sh"


def main():
    gt = json.loads((TASK / "tests" / "seal" / "gt.json").read_text(encoding="utf-8"))
    progs = {name: [list(s) for s in steps] for name, steps in cases.programs()}
    assert set(gt) == set(progs), "gt.json and cases.py name different programs"
    text = SH.read_text()
    answers = "ANSWERS = json.loads(%r)" % json.dumps(gt, sort_keys=True)
    programs = "PROGRAMS = json.loads(%r)" % json.dumps(progs, sort_keys=True)
    text, n1 = re.subn(r"^ANSWERS = json\.loads\(.*\)$", lambda m: answers, text, flags=re.M)
    text, n2 = re.subn(r"^PROGRAMS = json\.loads\(.*\)$", lambda m: programs, text, flags=re.M)
    assert n1 == 1 and n2 == 1, (n1, n2)
    assert "\r" not in text
    SH.write_text(text, newline="\n")
    print("forge-frozen carries %d programs with their frozen answers" % len(gt))


if __name__ == "__main__":
    main()
