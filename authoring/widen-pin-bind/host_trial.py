"""Emulate the two-container trial on this host, because Docker is not available here.

What the platform does and this reproduces: build the agent's tree, run its script inside it,
take the declared artifacts and nothing else, put them into a fresh verifier container at their
original paths, and run tests/test.sh. The isolation is reproduced as well: the worker runs
under the sandbox uid inside its own session under the wall clock, the reward directory is
root-owned and 0700 before anything submitted runs, and the sealed directory is 0700.

What it is not: a container. The kernel, the Python build and the filesystem are this host's,
so a result here is evidence about the task and not about the image.

It writes the real absolute paths the bundle uses, so only one copy may run at a time; the lock
is taken on a file outside the bundle. Every path handed in is resolved before anything chdirs,
and the exit status of everything it shells out to is checked.

    python3 -u authoring/widen-pin-bind/host_trial.py oracle
    python3 -u authoring/widen-pin-bind/host_trial.py nop
    python3 -u authoring/widen-pin-bind/host_trial.py --cheat cheat/cheat-sum-lowest.sh
    python3 -u authoring/widen-pin-bind/host_trial.py --dir authoring/widen-pin-bind/variants/undo-log
"""
import argparse
import fcntl
import json
import pathlib
import re
import shutil
import subprocess
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lab  # noqa: E402

APP = pathlib.Path("/app")
TESTS = pathlib.Path("/tests")
WORK = pathlib.Path("/work")
LOGS = pathlib.Path("/logs/verifier")
LOCK = pathlib.Path("/tmp/wpb-host-trial.lock")
ARTIFACTS = tuple("res/" + p for p in lab.PARTS)
SANDBOX = 1002


def sh(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def sandbox_user():
    got = sh(["getent", "passwd", str(SANDBOX)])
    if got.returncode != 0:
        made = sh(["useradd", "--uid", str(SANDBOX), "--no-create-home", "sandbox"])
        assert made.returncode == 0, made.stderr


def stage_agent():
    if APP.exists():
        shutil.rmtree(APP)
    shutil.copytree(lab.SRC, APP, ignore=shutil.ignore_patterns("__pycache__"))


def collect():
    """Only the declared artifacts cross into the verifier container."""
    kept = {}
    for rel in ARTIFACTS:
        one = APP / rel
        kept[rel] = one.read_bytes() if one.is_file() else None
    shutil.rmtree(APP)
    (APP / "res").mkdir(parents=True)
    for rel, blob in kept.items():
        if blob is not None:
            (APP / rel).write_bytes(blob)
    return sum(1 for blob in kept.values() if blob is not None)


def stage_verifier():
    for room in (TESTS, WORK, LOGS.parent):
        if room.exists():
            shutil.rmtree(room)
    shutil.copytree(lab.TASK / "tests", TESTS, ignore=shutil.ignore_patterns("__pycache__"))
    (TESTS / "test.sh").chmod(0o755)
    (TESTS / "seal").chmod(0o700)
    LOGS.mkdir(parents=True)
    WORK.mkdir()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("agent", nargs="?", default="oracle", choices=["oracle", "nop"])
    ap.add_argument("--cheat")
    ap.add_argument("--dir")
    args = ap.parse_args()

    cheat = pathlib.Path(args.cheat).resolve() if args.cheat else None
    overlay = pathlib.Path(args.dir).resolve() if args.dir else None
    if cheat is not None:
        assert cheat.is_file(), "no such cheat: %s" % cheat
    if overlay is not None:
        assert overlay.is_dir(), "no such directory: %s" % overlay

    LOCK.touch()
    with LOCK.open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        sandbox_user()
        stage_agent()

        t0 = time.time()
        if cheat is not None:
            got = sh(["bash", str(cheat)])
            assert got.returncode == 0, "cheat script failed: %s" % got.stderr[-400:]
            who = cheat.name
        elif overlay is not None:
            for part in lab.PARTS:
                shutil.copy(overlay / part, APP / "res" / part)
            who = overlay.name
        elif args.agent == "oracle":
            got = sh(["bash", str(lab.TASK / "solution" / "solve.sh")])
            assert got.returncode == 0, "solve.sh failed: %s" % got.stderr[-400:]
            who = "oracle"
        else:
            who = "nop"
        made = time.time() - t0

        taken = collect()
        stage_verifier()
        t0 = time.time()
        run = sh(["bash", str(TESTS / "test.sh")], cwd="/")
        ran = time.time() - t0
        reward = (LOGS / "reward.txt").read_text().strip() if (LOGS / "reward.txt").is_file() else "?"
        whole = run.stdout + run.stderr
        tail = [row for row in whole.splitlines() if row.strip()][-6:]
        worker = None
        for row in whole.splitlines():
            if row.startswith("half one exited "):
                worker = int(row.rsplit(" ", 1)[1])
        # The ctrf report names the test function but not the parameter, and which
        # enumerated program failed is the whole point of a layer report, so the names come
        # from pytest's own summary lines.
        # A fixture that calls pytest.fail is an ERROR rather than a FAILED, and an
        # unreadable record from half one is exactly that shape, so both are collected.
        failed = sorted(set(re.findall(r"^(?:FAILED|ERROR) [^:]+::(\S+)", whole, re.M)))
        if not failed and "error" in whole.lower() and reward != "1":
            failed = ["grader errored"]
        print("agent=%-26s artifacts=%d  agent_s=%.1f  verify_s=%.1f  reward=%s"
              % (who, taken, made, ran, reward))
        for row in tail:
            print("    | %s" % row)
        print("RESULT " + json.dumps({"who": who, "reward": reward, "worker": worker,
                                      "artifacts": taken, "failed": failed,
                                      "verify_s": round(ran, 1)}))
        return 0 if reward == "1" else 1


if __name__ == "__main__":
    raise SystemExit(main())
