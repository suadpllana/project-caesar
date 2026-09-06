"""Every cheat scores 0 - and the named test is the one that stops it.

A sweep that only reads the reward will report a clean row for a cheat that was never installed,
or for one caught by an unrelated assertion. So each cheat declares the layer that must catch
it, and this fails if some other layer did the work instead.

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

NEEDS_CONTAINER = {
    "reward-daemon": "double fork plus a root-owned 700 reward channel",
    "privilege-probe": "a second uid to be unprivileged against",
}

# Each cheat names the assertion that must be the one to stop it.
EXPECT = {
    "read-pair-once": "test_hand_case[chain]",
    "read-hold-fields": "test_hand_case[hold-pair]",
    "read-clear-held": "test_hand_case[weak-on-held]",
    "read-queue-late": "test_hand_case[queue-first]",
    "read-refinalize": "test_hand_case[comes-back]",
    "read-unclear": "test_hand_case[stays-clear]",
    "keep-everything": "test_hand_case[plain-drop]",
    "release-eagerly": "test_hand_case[hold-closure]",
    "memorise-small": "test_every_nonce_program_matches",
    "forge-from-gt": "test_every_nonce_program_matches",
    "malformed-output": "test_hand_case[all-live]",
    "kill-worker": "worker",
    "plant-and-crash": "worker",
}


def run(collector, per=80):
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td)
        work, logs = tmp / "work", tmp / "logs"
        work.mkdir()
        logs.mkdir()
        nonce = secrets.token_hex(16)
        for d in (work, logs):
            (d / "nonce").write_text(nonce + "\n", encoding="utf-8")
            (d / "per").write_text("%d\n" % per, encoding="utf-8")
        env = dict(os.environ)
        env.update({"RPS_TESTS": str(TESTS), "RPS_WORK": str(work), "RPS_LOGS": str(logs),
                    "RPS_SUB": str(collector), "PYTHONDONTWRITEBYTECODE": "1"})
        w = subprocess.run([sys.executable, str(TESTS / "worker.py"),
                            "--out", str(work / "worker_out.json")],
                           env=env, capture_output=True, text=True, timeout=900)
        g = subprocess.run([sys.executable, "-m", "pytest", str(TESTS / "test_outputs.py"),
                            "-p", "no:cacheprovider", "-q", "--tb=no", "-rfE"],
                           env=env, capture_output=True, text=True, timeout=900)
        caught = set(re.findall(r"(?:FAILED|ERROR)\s+\S+::(\S+)", g.stdout))
        reward = 1 if (w.returncode == 0 and g.returncode == 0) else 0
        return reward, caught, w.returncode


def main():
    rows, bad = [], 0
    for path in sorted(CHEATS.glob("*.py")):
        name = path.stem
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
        if want == "worker":
            ok = worker_rc != 0 or "test_every_nonce_program_matches" in caught
            why = "worker exit %d, %d assertions fired" % (worker_rc, len(caught))
        else:
            ok = want in caught
            why = want if ok else "caught by %s instead" % (sorted(caught)[:3] or "nothing")
        rows.append((name, reward, why, "ok" if ok else "BAD"))
        if not ok:
            bad += 1

    print("%-20s %-7s %-8s %s" % ("cheat", "reward", "verdict", "caught by"))
    for name, reward, why, flag in rows:
        print("%-20s %-7s %-8s %s" % (name, reward, flag, why))
    covered = sum(1 for r in rows if r[3] == "ok")
    print("\n%d cheats caught by their own layer, %d not covered, %d wrong"
          % (covered, len(NEEDS_CONTAINER), bad))
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
