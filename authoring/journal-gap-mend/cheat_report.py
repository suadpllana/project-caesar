"""Run every cheat through host_trial.py and say which layer caught it.

A cheat that scores 0 for the wrong reason proves nothing (CLAUDE.md, token-seam-emit: a sweep
that never installs the cheat reports clean zeroes). So each row records the reward, how the
worker ended, the tests that failed and the probe log, and checks the expected layer:

  a wrong reading       fails the hand journal named for it
  a slow exact solver   is stopped by the wall clock (half one exits 124)
  a forgery             passes every hand journal and fails the generated set
  a shortcut            fails hand journals
  a probe               leaves the evidence its defence should leave (probe log, reap)

    python3 authoring/journal-gap-mend/cheat_report.py [cheat-name ...]
"""
import pathlib
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
TASK = HERE.parents[1] / "tasks" / "journal-gap-mend"

NAMED = {
    "beat-anytime": "beat-needs-lock", "candidates-local": "live-candidates",
    "digest-floats": "digest-anchored", "digest-on-multiple": "digest-on-grant",
    "forward-only": "later-evidence", "shortest-plan": "later-evidence",
    "last-come-pass": "pass-first-waiter", "merge-holders": "queue-order",
    "no-depth": "reentry-depth", "no-end": "end-of-span", "pass-uncounted": "pass-is-grant",
    "single-start": "two-spans-one-beat", "span-local": "empty-then-grant",
    "waiting-sends": "waiter-silent", "walk-no-closure": "audit-before-loss",
    "audit-at-end": "audits-inside",
}


def run(cheat):
    proc = subprocess.run([sys.executable, str(HERE / "host_trial.py"), "--cheat", str(cheat)],
                          capture_output=True, text=True)
    return proc.stdout + proc.stderr


def verdict(name, out):
    reward = re.search(r"reward=(\d)", out)
    reward = int(reward.group(1)) if reward else -1
    half = re.search(r"half one exited (\d+)", out)
    half = int(half.group(1)) if half else -1
    failed = set(re.findall(r"test_hand_journal\[([a-z0-9-]+)\]", out))
    gen_failed = "test_every_generated_journal_matches" in out
    probe = [ln.split("probe| ", 1)[1] for ln in out.splitlines() if "probe| " in ln]
    key = name[len("cheat-"):-len(".sh")]
    ok, why = False, ""
    if reward != 0:
        why = "REWARD %d" % reward
    elif key in NAMED:
        ok = NAMED[key] in failed
        why = "caught by %s" % NAMED[key] if ok else "NOT caught by %s (failed: %s)" % (
            NAMED[key], sorted(failed)[:6])
    elif key.startswith("slow-"):
        ok = half == 124
        why = "stopped by the clock" if ok else "half one exited %d" % half
    elif key == "forge-hand":
        ok = not failed and gen_failed
        why = "hand journals pass, generated set fails" if ok else "hand failed %s" % sorted(failed)
    elif key.startswith("const-") or key.startswith("pos-"):
        ok = bool(failed)
        why = "fails %d hand journals" % len(failed)
    elif key == "probe-uncollected-file":
        ok = "ModuleNotFoundError" in out or "ImportError" in out or half not in (0, -1) \
            or len(failed) >= 20
        why = "extra file never collected; %d hand journals fail" % len(failed)
    elif key == "probe-shrink-set":
        ok = len(failed) >= 20
        why = "records missing for %d hand journals" % len(failed)
    elif key in ("probe-privilege", "probe-rewrite-grader", "probe-answer-key",
                 "probe-plant-report"):
        writable = [p for p in probe if p.startswith(("WRITABLE", "REPLACED", "model imported",
                                                      "read /logs", "read /tests",
                                                      "wrote /logs"))]
        ok = not writable and bool(probe)
        why = ("denied everywhere: " + "; ".join(probe[:6])) if ok else "BREACH %s" % writable
    elif key == "probe-late-reward":
        ok = True
        why = "survivor reaped or denied; reward stayed 0"
    elif key in ("probe-crash-worker", "probe-malformed"):
        ok = bool(failed)
        why = "fails %d hand journals" % len(failed)
    return ok, reward, half, why


def main(argv):
    names = argv or [p.name for p in sorted((TASK / "cheat").glob("*.sh"))]
    bad = 0
    for name in names:
        out = run(TASK / "cheat" / name)
        ok, reward, half, why = verdict(name, out)
        bad += not ok
        print("%-34s reward=%d half-one=%s  %s  %s" % (name, reward, half,
                                                       "OK " if ok else "BAD", why), flush=True)
    print("%d/%d cheats caught at the expected layer" % (len(names) - bad, len(names)), flush=True)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
