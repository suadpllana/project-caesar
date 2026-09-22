"""Run every cheat and report which layer caught it, not only the reward.

A cheat suite that reports eighteen clean zeroes proves nothing if the cheats were never
installed (CLAUDE.md, token-seam-emit): a script that failed to apply, a probe that attacks
before the runner is armed, a forgery that stopped working after the first program all score
0 for reasons that have nothing to do with the verifier. So every row here names the test that
failed, and the run fails when a cheat scores 0 with nothing failing, or when a reading is
caught by no enumerated case, or when a shortcut strategy matched more of the graded set than
the report expects.

Usage:
    python3 -u authoring/pull-check-stale/cheat_report.py [name-substring]
"""

import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import host_trial  # noqa: E402

TASK = HERE.parent.parent / "tasks" / "pull-check-stale"
CHEATS = sorted((TASK / "cheat").glob("cheat-*.sh"))

FAILED = re.compile(r"(?:FAILED|ERROR)\s+\S*test_outputs\.py::(\S+)")
NONCE = re.compile(r"(\d+) of (\d+) nonce programs wrong")


def layer(text):
    hand, other, nonce = [], [], None
    for name in FAILED.findall(text):
        if name.startswith("test_hand_case["):
            hand.append(name[len("test_hand_case["):-1])
        else:
            other.append(name)
    m = NONCE.search(text)
    if m:
        nonce = (int(m.group(1)), int(m.group(2)))
    return hand, sorted(set(other)), nonce


def main(argv):
    only = argv[1] if len(argv) > 1 else ""
    rows = []
    bad = []
    for path in CHEATS:
        name = path.stem[len("cheat-"):]
        if only and only not in name:
            continue
        reward, spent, worker, grade = host_trial.trial(
            "script", str(path.relative_to(HERE.parent.parent)), quiet=True)
        hand, other, nonce = layer(grade.stdout + grade.stderr)
        rows.append((name, reward, spent, hand, other, nonce, worker.returncode))
        note = ""
        if nonce:
            note = "  nonce %d/%d wrong" % nonce
        print("%-24s reward %d  %5.1fs  hand %-2d %s%s"
              % (name, reward, spent, len(hand),
                 (hand[0] if hand else (other[0] if other else "NOTHING FAILED")), note),
              flush=True)
        if reward != 0:
            bad.append("%s scored 1" % name)
        elif not hand and not other and worker.returncode == 0:
            bad.append("%s scored 0 with nothing failing - it may not have been installed"
                       % name)
        elif name in NOT_BY_WORKER and worker.returncode != 0:
            bad.append("%s was caught by the worker dying, not by the grader" % name)
        elif name in READING_NAMES and not hand:
            bad.append("%s is caught by no enumerated case - the set does not name that rule"
                       % name)
    print()
    if bad:
        print("FINDINGS")
        for b in bad:
            print("  %s" % b)
        return 1
    print("all %d cheats score 0, each caught by a named test" % len(rows))
    return 0


READING_NAMES = {
    "chk-all", "chk-flat-first", "memo-round", "no-stuck", "stuck-on-check", "look-as-read",
    "look-blind", "fail-forget", "fail-sticky", "rec-merge", "no-cutoff", "read-pulls",
    "no-out-mark", "loop-from-root", "loop-no-close", "via-inner", "dead-reason-match",
    "run-line-after", "cut-tombstone", "emit-reads-only", "miss-no-mark",
}

# Cheats that must be caught by the grader reading a wrong trace, not by the worker falling
# over: a probe that only ever crashes the worker has not been shown to be contained.
NOT_BY_WORKER = READING_NAMES | {
    "flat-one-answer", "flat-first-seed", "flat-run-everything", "flat-replay-example",
    "forge-answer-key",
}


if __name__ == "__main__":
    sys.exit(main(sys.argv))
