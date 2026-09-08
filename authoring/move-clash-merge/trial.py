"""Host emulation of the two-container trial. Says plainly what it cannot cover.

Runs the real `plant.py`, the real `runner.py` and the real `test_outputs.py` against a chosen
policy directory and derives the reward the way `test.sh` does: default 0, and 1 only when the
run and the grader both came back clean, inside the same execution limit the container enforces.

WHAT THIS DOES NOT COVER, and only a container can: the privilege drop to uid 1004, the
root-owned 700 reward channel, the root-only mode bits on the model and the ground truth,
/proc survivor reaping and the process-group kill. The cheats aimed squarely at those are
reported as not covered rather than as passes.

    python authoring/move-clash-merge/trial.py oracle
    python authoring/move-clash-merge/trial.py --all
    python authoring/move-clash-merge/trial.py --dir authoring/move-clash-merge/variants/flat
"""
import argparse
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
TASK = ROOT / "tasks" / "move-clash-merge"
TESTS = TASK / "tests"
HERE = ROOT / "authoring" / "move-clash-merge"
PARTS = ("live.py", "spot.py", "name.py", "book.py", "step.py")

NOT_COVERED = ("reward-daemon", "privilege-probe")

# Must match `timeout --signal=KILL N` in tests/test.sh: the stated execution limit.
RUN_LIMIT = 600


def detail(policy, count=60):
    """Reward, plus which grader tests failed and how the run itself exited."""
    return _run(policy, count)


def score(policy, count=60, quiet=True):
    reward, failed, status = _run(policy, count)
    if not quiet and reward == 0:
        print("      run exit %s; failed: %s" % (status, ", ".join(failed) or "none"))
    return reward


def _run(policy, count):
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td)
        work, logs = tmp / "app", tmp / "logs"
        run = tmp / "run"
        run.mkdir()
        logs.mkdir()
        shutil.copytree(TESTS / "pristine", work,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        for part in PARTS:
            one = pathlib.Path(policy) / part
            if one.is_file():
                shutil.copy(one, work / "mrg" / part)
        nonce = os.urandom(12).hex()
        (logs / "nonce").write_text(nonce + "\n", encoding="utf-8")

        env = dict(os.environ)
        env.update({
            "PYTHONPATH": str(TESTS),
            "PYTHONDONTWRITEBYTECODE": "1",
            "APPDIR": str(work),
            "PLAN": str(run / "plan.json"),
            "RUN_OUT": str(run / "out.json"),
            "RUN_NONCE": nonce,
            "RUN_COUNT": str(count),
            "PRISTINE_DIR": str(TESTS / "pristine"),
            "NONCE_FILE": str(logs / "nonce"),
            "REQUIRE_MONITORING": "1",
        })
        plant = subprocess.run([sys.executable, str(TESTS / "plant.py"), str(run / "plan.json")],
                               env=env, capture_output=True, text=True)
        if plant.returncode != 0:
            print(plant.stderr[-800:])
            return 0
        # The container hands the run a descriptor root opened, never a writable path.
        # Emulating that is what makes a report-planting probe meaningful here.
        handle = os.open(str(run / "out.json"), os.O_RDWR | os.O_CREAT | os.O_TRUNC, 0o600)
        try:
            worker = subprocess.run([sys.executable, str(TESTS / "runner.py"),
                                     "fd:%d" % handle],
                                    env=env, capture_output=True, text=True, timeout=RUN_LIMIT,
                                    pass_fds=(handle,))
            run_status = worker.returncode
        except subprocess.TimeoutExpired:
            run_status = 124
        finally:
            os.close(handle)
        graded = subprocess.run([sys.executable, "-m", "pytest", str(TESTS / "test_outputs.py"),
                                 "-p", "no:cacheprovider", "-q", "-rfE"],
                                env=env, capture_output=True, text=True, timeout=1800)
        reward = 1 if (run_status == 0 and graded.returncode == 0) else 0
        failed = []
        for line in graded.stdout.splitlines():
            if line.startswith("FAILED ") or line.startswith("ERROR "):
                head = line.split(" ", 1)[1].split(" ")[0]
                failed.append(head.split("::")[-1].split("[")[0])
        return reward, sorted(set(failed)), run_status


def suites():
    out = {"oracle": (TASK / "solution", 1),
           "nop": (TASK / "environment" / "app_src" / "mrg", 0)}
    for kind, want in (("variants", 1), ("cheats", 0)):
        where = HERE / kind
        if where.is_dir():
            for one in sorted(x for x in where.iterdir() if x.is_dir()):
                out["%s:%s" % (kind[:-1], one.name)] = (one, want)
    return out


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("which", nargs="?")
    ap.add_argument("--dir")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--count", type=int, default=60)
    a = ap.parse_args(argv[1:])

    if a.dir:
        print(score(pathlib.Path(a.dir), a.count, quiet=False))
        return 0

    every = suites()
    picked = every if a.all else {a.which: every[a.which]}
    off = 0
    for name in sorted(picked):
        path, want = picked[name]
        if name.startswith("cheat:") and name.split(":", 1)[1] in NOT_COVERED:
            print("%-34s not covered by host emulation (needs a container)" % name)
            continue
        got = score(path, a.count, quiet=not a.all)
        if got != want:
            off += 1
        print("%-34s reward %d  want %d  %s"
              % (name, got, want, "ok" if got == want else "WRONG"))
    print("\n%d of %d off" % (off, len(picked)))
    return 1 if off else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
