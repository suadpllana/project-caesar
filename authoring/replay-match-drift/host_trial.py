"""Run the real two-stage verifier on this host, because image pulls are blocked here.

The platform runs the agent in one container and `tests/test.sh` in another. Docker is
running in this session but the registry CDN is refused by the egress policy, so no base
image can be pulled and no container evidence exists. This is the closest honest stand-in:
the shipped `tests/test.sh` is executed verbatim, at the real paths, with the real
privilege drop onto uid 1002, the real root-owned 0700 reward directory and the real
0700 seal - and with artifact collection emulated exactly as the harness does it, so only
the six declared files survive the trip from the agent's tree to the verifier's.

What it does NOT prove: that either image builds, or that anything is isolated by a
container boundary. `tools/imagecheck.py` covers the first; the second is recorded as
unavailable in STATE.md rather than claimed.

Usage:
    python3 authoring/replay-match-drift/host_trial.py oracle
    python3 authoring/replay-match-drift/host_trial.py nop
    python3 authoring/replay-match-drift/host_trial.py --cheat <path/to/cheat.sh>
    python3 authoring/replay-match-drift/host_trial.py --dir authoring/replay-match-drift/variants/ok-flat
    python3 authoring/replay-match-drift/host_trial.py --all
"""
import fcntl
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
TASK = ROOT / "tasks" / "replay-match-drift"
LOCK = pathlib.Path("/tmp/replay-match-drift.trial.lock")
APP = pathlib.Path("/app")
TESTS = pathlib.Path("/tests")
WORK = pathlib.Path("/work")
LOGS = pathlib.Path("/logs/verifier")


def declared():
    text = (TASK / "task.toml").read_text(encoding="utf-8")
    block = text.split("artifacts", 1)[1].split("]", 1)[0]
    return [m.group(1) for m in re.finditer(r'"([^"]+)"', block)]


def ensure_uid():
    if subprocess.run(["getent", "passwd", "1002"], capture_output=True).returncode:
        subprocess.run(["useradd", "--no-create-home", "--uid", "1002", "plain"], check=True)


def lay_agent():
    """The agent's container: /app and nothing else. The verifier's tree does not exist yet."""
    for path in (APP, TESTS, WORK, LOGS):
        if path.exists():
            shutil.rmtree(path, ignore_errors=True)
    shutil.copytree(TASK / "environment" / "app_src", APP)


def lay_verifier():
    """The verifier's container, built after the agent's is gone, as the platform does."""
    shutil.copytree(TASK / "tests", TESTS, ignore=shutil.ignore_patterns("__pycache__"))
    (TESTS / "seal").chmod(0o700)
    LOGS.mkdir(parents=True, exist_ok=True)


def collect():
    """Only the declared artifacts cross from the agent's tree to the verifier's."""
    held = pathlib.Path(tempfile.mkdtemp())
    kept = []
    for spec in declared():
        src = pathlib.Path(spec)
        if src.is_file():
            dst = held / spec.lstrip("/")
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(src, dst)
            kept.append(spec)
    shutil.rmtree(APP, ignore_errors=True)
    APP.mkdir(parents=True)
    for spec in kept:
        dst = pathlib.Path(spec)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(held / spec.lstrip("/"), dst)
    shutil.rmtree(held)
    return kept


def run_agent(how, arg):
    if how == "nop":
        return 0, "nop: the shipped tree, untouched"
    if how == "dir":
        for part in ("tab", "edge", "pair", "pend", "sigq", "ver"):
            one = pathlib.Path(arg) / (part + ".py")
            if one.is_file():
                shutil.copy(one, APP / "dur" / (part + ".py"))
        return 0, "copied %s over /app/dur" % arg
    script = pathlib.Path(arg).resolve()
    done = subprocess.run(["bash", str(script)], cwd="/app", capture_output=True, text=True)
    return done.returncode, (done.stdout + done.stderr).strip()[-400:]


def trial(how, arg, label):
    ensure_uid()
    lay_agent()
    rc, note = run_agent(how, arg)
    kept = collect()
    lay_verifier()
    done = subprocess.run(["bash", str(TESTS / "test.sh")], capture_output=True, text=True)
    reward = (LOGS / "reward.txt").read_text(encoding="utf-8").strip() \
        if (LOGS / "reward.txt").is_file() else "MISSING"
    tail = (done.stdout + done.stderr).strip().splitlines()
    print("%-34s reward %s   agent exit %s   files collected %d"
          % (label, reward, rc, len(kept)))
    return reward, note, tail


def main():
    with open(LOCK, "w") as fh:
        fcntl.flock(fh, fcntl.LOCK_EX)
        argv = sys.argv[1:]
        rows = []
        if argv and argv[0] == "--all":
            rows.append(("script", str(TASK / "solution" / "solve.sh"), "oracle"))
            rows.append(("nop", "", "nop"))
            for sh in sorted((TASK / "cheat").glob("*.sh")):
                rows.append(("script", str(sh), sh.stem))
        elif argv and argv[0] == "--cheat":
            rows.append(("script", argv[1], pathlib.Path(argv[1]).stem))
        elif argv and argv[0] == "--dir":
            rows.append(("dir", argv[1], pathlib.Path(argv[1]).name))
        elif argv and argv[0] == "nop":
            rows.append(("nop", "", "nop"))
        else:
            rows.append(("script", str(TASK / "solution" / "solve.sh"), "oracle"))

        bad = 0
        for how, arg, label in rows:
            reward, note, tail = trial(how, arg, label)
            want = "1" if label in ("oracle",) or label.startswith("ok-") else "0"
            if reward != want:
                bad += 1
                print("   WANTED %s" % want)
                for row in tail[-14:]:
                    print("   | %s" % row)
        return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
