"""Which enumerated case catches a reading that the limit catches first.

Four of the wrong readings are also slow: the conflict rule walks every holder for every
blocked request, the barrier reading lets the queue grow without bound, and granting a raise
in the mark it asked for keeps letting more requests onto an item, so on the two large
families they miss the limit before the grader ever compares a trace. Scoring 0 by the
limit is a real result, but it is not the result those cheats were written for. Run with the
large families out of the population and the enumerated case that names each one shows up.
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
CHEATS = HERE.parent.parent / "tasks" / "claim-raise-cut" / "cheat"

WANT = {
    "edge-conflict": "edge-miss",
    "edge-and": "edge-phantom",
    "pin-bar": "raise-pass",
    "raise-ask-mark": "join-pair",
}


def main():
    room = Path(tempfile.mkdtemp(prefix="crc-small-"))
    bad = []
    for name, want in sorted(WANT.items()):
        out = room / (name + ".json")
        subprocess.run(
            [sys.executable, "-u", str(HERE / "host_trial.py"),
             "--script", str(CHEATS / ("cheat-%s.sh" % name)),
             "--per", "4", "--heavy", "0", "--json", str(out)],
            capture_output=True, text=True, cwd=str(HERE.parent.parent))
        try:
            res = json.loads(out.read_text(encoding="utf-8"))
        except Exception as exc:
            bad.append("%s produced no result: %s" % (name, exc))
            continue
        cases = [f.split("[", 1)[1].rstrip("]") for f in res.get("failed", [])
                 if f.startswith("test_hand_case[")]
        ok = res.get("reward") == 0 and want in cases
        print("%-14s reward %s  want %-14s caught by %d cases: %s"
              % (name, res.get("reward"), want, len(cases), ", ".join(cases[:5])), flush=True)
        if not ok:
            bad.append("%s: reward %s, cases %s" % (name, res.get("reward"), cases[:5]))
    for line in bad:
        print("FINDING:", line)
    print("%d readings, %d findings" % (len(WANT), len(bad)))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
