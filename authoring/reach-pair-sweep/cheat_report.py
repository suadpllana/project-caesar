"""Every cheat scores 0 - and the named layer is the one that stops it.

A sweep that only reads the reward reports a clean row for a cheat that was never installed, or
for one caught by an unrelated assertion. So each cheat declares the layer that must catch it,
and this fails if something else did the work instead.

    python authoring/reach-pair-sweep/cheat_report.py
"""
import os
import pathlib
import re
import secrets
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
TASK = ROOT / "tasks" / "reach-pair-sweep"
TESTS = TASK / "tests"
CHEATS = ROOT / "authoring" / "reach-pair-sweep" / "cheats"

LIMIT = 60
PER = 60

NEEDS_CONTAINER = {
    "reward-daemon": "double fork plus a root-owned 700 reward channel",
    "privilege-probe": "a second uid to be unprivileged against",
}

EXPECT = {
    "read-no-rset": "test_hand_case[rset-root]",
    "read-trust-rset": "test_hand_case[rset-stale]",
    "read-old-key-unready": "test_hand_case[old-key]",
    "read-queue-late": "test_hand_case[queue-first]",
    "read-age-held": "test_hand_case[held-no-age]",
    "read-wipe-old": "test_hand_case[weak-old]",
    "read-release-old": "test_hand_case[old-safe]",
    "keep-everything": "test_hand_case[plain-drop]",
    "release-eagerly": "test_hand_case[hold-closure]",
    "malformed-output": "test_hand_case[all-live]",
    "forge-from-gt": "test_every_nonce_program_matches",
    "rescan-pairs": "limit",
    "kill-worker": "worker",
    "plant-and-crash": "worker",
}


def run(collector):
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td)
        work, logs = tmp / "work", tmp / "logs"
        work.mkdir()
        logs.mkdir()
        nonce = secrets.token_hex(16)
        for d in (work, logs):
            (d / "nonce").write_text(nonce + "\n", encoding="utf-8")
            (d / "per").write_text("%d\n" % PER, encoding="utf-8")
        env = dict(os.environ)
        env.update({"RPS_TESTS": str(TESTS), "RPS_WORK": str(work), "RPS_LOGS": str(logs),
                    "RPS_SUB": str(collector), "PYTHONDONTWRITEBYTECODE": "1"})
        try:
            w = subprocess.run([sys.executable, str(TESTS / "worker.py"),
                                "--out", str(work / "worker_out.json")],
                               env=env, capture_output=True, text=True, timeout=LIMIT)
            worker_rc = w.returncode
        except subprocess.TimeoutExpired:
            worker_rc = 124
        g = subprocess.run([sys.executable, "-m", "pytest", str(TESTS / "test_outputs.py"),
                            "-p", "no:cacheprovider", "-q", "--tb=no", "-rfE"],
                           env=env, capture_output=True, text=True, timeout=900)
        caught = set(re.findall(r"(?:FAILED|ERROR)\s+\S+::(\S+)", g.stdout))
        reward = 1 if (worker_rc == 0 and g.returncode == 0) else 0
        return reward, caught, worker_rc


def main():
    rows, bad = [], 0
    for path in sorted(p for p in CHEATS.iterdir() if p.is_dir()):
        name = path.name
        if name in NEEDS_CONTAINER:
            rows.append((name, "-", "not covered: needs %s" % NEEDS_CONTAINER[name], "skip"))
            continue
        want = EXPECT.get(name)
        if want is None:
            rows.append((name, "?", "no declared catcher", "BAD"))
            bad += 1
            continue
        reward, caught, worker_rc = run(path)
        if reward != 0:
            rows.append((name, reward, "scored 1", "BAD"))
            bad += 1
            continue
        if want == "limit":
            ok = worker_rc != 0
            why = "worker exceeded the %ds limit (exit %d)" % (LIMIT, worker_rc)
        elif want == "worker":
            ok = worker_rc != 0 or "test_every_nonce_program_matches" in caught
            why = "worker exit %d, %d assertions fired" % (worker_rc, len(caught))
        else:
            ok = want in caught
            why = want if ok else "caught by %s instead" % (sorted(caught)[:3] or "nothing")
        rows.append((name, reward, why, "ok" if ok else "BAD"))
        if not ok:
            bad += 1

    print("%-22s %-7s %-8s %s" % ("cheat", "reward", "verdict", "caught by"))
    for name, reward, why, flag in rows:
        print("%-22s %-7s %-8s %s" % (name, reward, flag, why))
    covered = sum(1 for r in rows if r[3] == "ok")
    print("\n%d cheats caught by their own layer, %d not covered, %d wrong"
          % (covered, len(NEEDS_CONTAINER), bad))
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
