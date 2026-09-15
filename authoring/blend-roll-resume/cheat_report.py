"""Run every cheat, and assert the layer that caught it rather than only the reward.

A cheat scoring 0 says nothing on its own: a forgery that stopped working after the first
script, or a probe that also happens to do the work correctly, both report 0 and neither has
tested what it was written to test. So each row records which graded tests failed, and the
expectations below name them.

    python3 authoring/blend-roll-resume/cheat_report.py
"""
import json
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
TASK = ROOT / "tasks" / "blend-roll-resume"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(TASK / "tests"))

import cases  # noqa: E402
import host_trial  # noqa: E402

NONCE = "test_every_nonce_script_matches"
FAMILIES = "test_every_family_is_represented"

# What each cheat has to be caught by, beyond scoring 0.
#   hand           at least one enumerated case must fail
#   nonce          the generated population must fail
#   all_hand_pass  every enumerated case must PASS - the point of a forgery
#   worker_gone    the run must have produced no record at all (the clock, or a kill)
EXPECT = {
    "cheat-forge-from-truth.sh": {"nonce", "all_hand_pass"},
    "cheat-slow-per-draw.sh": {"worker_gone"},
    "cheat-slow-per-step.sh": {"worker_gone"},
    "cheat-probe-kill-grader.sh": {"worker_gone"},
    # These two plant a record and leave cleanly, so a record does exist. What has to hold is
    # that the grader derived its verdict from the model rather than from the plant.
    "cheat-probe-exit-clean.sh": {"hand"},
    "cheat-probe-malformed.sh": {"hand"},
}
DEFAULT = {"hand"}


def failures(name):
    path = Path("/tmp/brr-reports") / ("cheat: %s.json" % name)
    if not path.is_file():
        return None
    try:
        report = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    out = []
    for test in report.get("results", {}).get("tests", []):
        if test.get("status") not in ("passed", "skipped"):
            out.append(test.get("name", "?"))
    return out


def worker_present(name):
    path = Path("/tmp/brr-reports") / ("cheat: %s.worker" % name)
    return path.is_file() and path.read_text(encoding="utf-8").strip() == "present"


def note(name, key):
    path = Path("/tmp/brr-reports") / ("cheat: %s.%s" % (name, key))
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def main():
    shutil.rmtree("/tmp/brr-reports", ignore_errors=True)
    cheats = sorted((TASK / "cheat").glob("cheat-*.sh"))
    if not cheats:
        print("no cheats to run")
        return 1
    bad = []
    with open(host_trial.LOCK, "w") as fh:
        import fcntl
        fcntl.flock(fh, fcntl.LOCK_EX)
        for sh in cheats:
            ok = host_trial.trial("cheat: " + sh.name, sh, 0)
            want = EXPECT.get(sh.name, DEFAULT)
            fails = failures(sh.name)
            hand = [f for f in (fails or []) if "test_hand_case" in f]
            if not ok:
                bad.append((sh.name, "scored 1"))
                continue
            if "worker_gone" in want:
                if worker_present(sh.name):
                    bad.append((sh.name, "expected the run to leave no record, it left one"))
                continue
            if fails is None:
                bad.append((sh.name, "no grading report to read"))
                continue
            if "all_hand_pass" in want and hand:
                bad.append((sh.name, "reproduced only part of the frozen answers: %d of %d "
                                     "enumerated scripts failed" % (len(hand), len(cases.ORDER))))
            if "nonce" in want and not any(NONCE in f for f in fails):
                bad.append((sh.name, "was not caught by the generated population"))
            if "hand" in want and not hand:
                bad.append((sh.name, "no enumerated case failed it - the set does not name it"))

    key = note("cheat-probe-answer-key.sh", "brr-key.txt")
    if "PermissionError" not in key:
        bad.append(("cheat-probe-answer-key.sh",
                    "reached the sealed answers instead of being refused: %r" % key[:80]))
    priv = note("cheat-probe-privilege.sh", "brr-priv.txt")
    for want in ("uid 1002", "/logs/verifier/reward.txt PermissionError",
                 "/tests/seal/model.py PermissionError"):
        if want not in priv:
            bad.append(("cheat-probe-privilege.sh", "did not record %r: %r" % (want, priv[:120])))

    for name, why in bad:
        print("FINDING %s: %s" % (name, why))
    print("%d cheats, %d scored 0 and were caught where they should be"
          % (len(cheats), len(cheats) - len({n for n, _ in bad})))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
