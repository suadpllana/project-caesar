"""Host emulation of the two-container trial. Says plainly what it cannot cover.

Runs the real `worker.py` and the real `test_outputs.py` against a chosen collector directory
and derives the reward the way `test.sh` does: default 0, and 1 only when both the worker and
the grader came back clean, inside the same execution limit the container enforces.

WHAT THIS DOES NOT COVER, and only a container can: the privilege drop to uid 1002, the
root-owned 700 reward channel, `/proc` survivor reaping, and the process-group kill. The two
cheats aimed squarely at those - `reward-daemon`, which needs fork, and `privilege-probe`, which
needs a second uid - are reported as not covered rather than as passes.

    python authoring/reach-pair-sweep/trial.py oracle
    python authoring/reach-pair-sweep/trial.py --all
    python authoring/reach-pair-sweep/trial.py --dir authoring/reach-pair-sweep/variants/alt
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
HERE = ROOT / "authoring" / "reach-pair-sweep"

NOT_COVERED = ("reward-daemon", "privilege-probe", "read-sealed-model")

# Must match `timeout N setsid` in tests/test.sh: the stated execution limit.
WORKER_LIMIT = 60


def score(collector, per=60, quiet=True):
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

        # `test.sh` prepares the worker's inputs on the trusted side first. Emulate that same
        # step here; skipping it leaves the worker with no programs and scores every collector 0.
        prep = subprocess.run([sys.executable, str(TESTS / "prepare.py"),
                               "--nonce-file", str(logs / "nonce"),
                               "--per-file", str(logs / "per"),
                               "--out", str(work / "programs.json"),
                               "--tree", str(work / "pristine")],
                              cwd=str(TESTS), env=env, capture_output=True, text=True)
        if prep.returncode != 0:
            raise SystemExit("prepare.py failed:\n" + prep.stderr)

        try:
            w = subprocess.run([sys.executable, str(TESTS / "worker.py"),
                                "--out", str(work / "worker_out.json")],
                               env=env, capture_output=True, text=True, timeout=WORKER_LIMIT)
            worker_rc = w.returncode
        except subprocess.TimeoutExpired:
            worker_rc = 124
        g = subprocess.run([sys.executable, "-m", "pytest", str(TESTS / "test_outputs.py"),
                            "-p", "no:cacheprovider", "-q"],
                           env=env, capture_output=True, text=True, timeout=900)
        reward = 1 if (worker_rc == 0 and g.returncode == 0) else 0
        if not quiet and reward == 0:
            print("\n".join("      " + ln
                            for ln in [x for x in g.stdout.splitlines() if x.strip()][-6:]))
        return reward


def collectors():
    out = {"oracle": (TASK / "solution", 1),
           "nop": (TASK / "environment" / "app_src" / "col", 0)}
    for kind, want in (("variants", 1), ("cheats", 0)):
        d = HERE / kind
        if d.is_dir():
            for p in sorted(x for x in d.iterdir() if x.is_dir()):
                out["%s:%s" % (kind[:-1], p.name)] = (p, want)
    return out


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("which", nargs="?")
    ap.add_argument("--dir")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--per", type=int, default=60)
    a = ap.parse_args(argv[1:])

    if a.dir:
        print(score(pathlib.Path(a.dir), a.per, quiet=False))
        return 0

    every = collectors()
    picked = every if a.all else {a.which: every[a.which]}
    bad = 0
    for name in sorted(picked):
        path, want = picked[name]
        if name.startswith("cheat:") and name.split(":", 1)[1] in NOT_COVERED:
            print("%-30s not covered by host emulation (needs a container)" % name)
            continue
        got = score(path, a.per, quiet=not a.all)
        if got != want:
            bad += 1
        print("%-30s reward %d  want %d  %s" % (name, got, want,
                                                "ok" if got == want else "WRONG"))
    print("\n%d of %d off" % (bad, len(picked)))
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
