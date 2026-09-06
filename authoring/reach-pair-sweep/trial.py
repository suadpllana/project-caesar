"""Host emulation of the two-container trial. Says plainly what it cannot cover.

Runs the real `worker.py` and the real `test_outputs.py` against a chosen collector and derives
the reward the way `test.sh` does: default 0, and 1 only when both the worker and the grader
came back clean.

WHAT THIS DOES NOT COVER, and only a container can: the privilege drop to uid 1002, the
root-owned 700 reward channel, `/proc` survivor reaping, and the process-group kill. The two
cheats aimed squarely at those - `reward-daemon`, which needs fork, and `privilege-probe`,
which needs a second uid - are reported as not covered rather than as passes. `kill-worker`
and `plant-and-crash` do run here: they attack the worker stage, which this reproduces, though
on the host they degrade to a plain early exit because the container paths are absent.

    python authoring/reach-pair-sweep/trial.py oracle
    python authoring/reach-pair-sweep/trial.py nop
    python authoring/reach-pair-sweep/trial.py --file some/keep.py
    python authoring/reach-pair-sweep/trial.py --all
"""
import argparse
import os
import pathlib
import secrets
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
TASK = ROOT / "tasks" / "reach-pair-sweep"
TESTS = TASK / "tests"

NOT_COVERED = ("reward-daemon", "privilege-probe")


def score(collector, per=80, quiet=True):
    """Reward for one collector, by the same default-deny rule test.sh uses."""
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td)
        work, logs = tmp / "work", tmp / "logs"
        work.mkdir()
        logs.mkdir()
        (logs / "nonce").write_text(secrets.token_hex(16) + "\n", encoding="utf-8")
        (logs / "per").write_text("%d\n" % per, encoding="utf-8")
        (work / "nonce").write_text((logs / "nonce").read_text(encoding="utf-8"),
                                    encoding="utf-8")
        (work / "per").write_text((logs / "per").read_text(encoding="utf-8"), encoding="utf-8")

        env = dict(os.environ)
        env.update({"RPS_TESTS": str(TESTS), "RPS_WORK": str(work), "RPS_LOGS": str(logs),
                    "RPS_SUB": str(collector), "PYTHONDONTWRITEBYTECODE": "1"})

        w = subprocess.run([sys.executable, str(TESTS / "worker.py"),
                            "--out", str(work / "worker_out.json")],
                           env=env, capture_output=True, text=True, timeout=900)
        g = subprocess.run([sys.executable, "-m", "pytest", str(TESTS / "test_outputs.py"),
                            "-p", "no:cacheprovider", "-q"],
                           env=env, capture_output=True, text=True, timeout=900)
        reward = 1 if (w.returncode == 0 and g.returncode == 0) else 0
        if not quiet and reward == 0:
            tail = [ln for ln in g.stdout.splitlines() if ln.strip()][-6:]
            print("\n".join("      " + ln for ln in tail))
        return reward


def collectors():
    out = {"oracle": (TASK / "solution" / "keep.py", 1),
           "nop": (TASK / "environment" / "app_src" / "cyc" / "keep.py", 0)}
    d = ROOT / "authoring" / "reach-pair-sweep" / "variants"
    if d.is_dir():
        for p in sorted(d.glob("*.py")):
            out["variant:" + p.stem] = (p, 1)
    d = ROOT / "authoring" / "reach-pair-sweep" / "cheats"
    if d.is_dir():
        for p in sorted(d.glob("*.py")):
            out["cheat:" + p.stem] = (p, 0)
    return out


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("which", nargs="?")
    ap.add_argument("--file")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--per", type=int, default=80)
    a = ap.parse_args(argv[1:])

    if a.file:
        print(score(pathlib.Path(a.file), a.per, quiet=False))
        return 0

    every = collectors()
    picked = every if a.all else {a.which: every[a.which]}
    bad = 0
    for name in sorted(picked):
        path, want = picked[name]
        if name.startswith("cheat:") and name.split(":", 1)[1] in NOT_COVERED:
            print("%-28s not covered by host emulation (needs a container)" % name)
            continue
        got = score(path, a.per, quiet=not a.all)
        flag = "ok" if got == want else "WRONG"
        if got != want:
            bad += 1
        print("%-28s reward %d  want %d  %s" % (name, got, want, flag))
    print("\n%d of %d off" % (bad, len(picked)))
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
