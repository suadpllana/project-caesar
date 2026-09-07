"""Run the shipped tests/test.sh itself, on this host, at the paths it expects.

The plain host emulation in trial.py skips everything that makes the verifier safe: it
never drops privileges, never locks the reward channel and never makes the answers
root-only, so it cannot say anything about a cheat that goes after the reward rather than
the answer. This does all of that, by laying the verifier image's layout onto the host
(/tests, /pristine, /app, /work, /logs) and running the real script unmodified.

It is still not the container gate - no image is built, and the host kernel is shared -
but the privilege drop, the root-owned reward directory, the 600 ground truth, the session
and the reaping are the shipped ones, so the isolation cheats are exercised for real.

    python authoring/sheet-block-place/sealed.py oracle
    python authoring/sheet-block-place/sealed.py nop
    python authoring/sheet-block-place/sealed.py --dir <policy dir>
    python authoring/sheet-block-place/sealed.py --cheats
"""

import os
import pathlib
import pwd
import shutil
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
TASK = HERE.parents[1] / "tasks" / "sheet-block-place"
TESTS = TASK / "tests"
POLICY = ("val.py", "see.py", "lay.py", "memo.py")
UID = 1004
USER = "sweep"


def account():
    try:
        pwd.getpwnam(USER)
        return
    except KeyError:
        pass
    subprocess.run(["useradd", "-u", str(UID), "-M", "-s", "/usr/sbin/nologin", USER],
                   check=True, capture_output=True)


def lay_out(overlay):
    for p in ("/tests", "/pristine", "/app", "/work", "/logs"):
        shutil.rmtree(p, ignore_errors=True)
    shutil.copytree(TESTS, "/tests", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    shutil.move("/tests/pristine", "/pristine")
    os.makedirs("/app/sheet", exist_ok=True)
    os.makedirs("/logs", exist_ok=True)
    if overlay:
        for name in POLICY:
            src = pathlib.Path(overlay) / name
            if src.exists():
                shutil.copyfile(src, "/app/sheet/" + name)
    os.chmod("/tests", 0o755)
    for name in ("gt.json", "oracle.py", "test_outputs.py"):
        os.chmod("/tests/" + name, 0o600)
        os.chown("/tests/" + name, 0, 0)
    for name in ("runner.py", "gen.py", "cases.py", "reap.py"):
        os.chmod("/tests/" + name, 0o644)


def clean():
    for p in ("/tests", "/pristine", "/app", "/work", "/logs"):
        shutil.rmtree(p, ignore_errors=True)


def run(overlay, count, script=None):
    """overlay lays four files straight in; script runs a cheat's own shell script the way
    the harness would run solve.sh, so the cheat is exercised as it ships."""
    account()
    lay_out(overlay)
    if script is not None:
        made = subprocess.run(["bash", str(script)], capture_output=True, text=True,
                              timeout=600)
        if made.returncode != 0:
            clean()
            return "script failed", made.stderr[-200:], []
    # /opt/v312 is a 3.12 virtualenv carrying the same pinned pytest and ctrf plugin the
    # verifier image installs. The host's default interpreter is 3.11, which has no
    # sys.monitoring, so without this the run falls back to the profile hook and the
    # instrumentation check fails for a reason the image would never see.
    env = dict(os.environ, RUN_COUNT=str(count), PYTHONPATH="/tests",
               PYTHONDONTWRITEBYTECODE="1",
               PATH="/opt/v312/bin:/usr/local/bin:/usr/bin:/bin")
    proc = subprocess.run(["bash", str(TESTS / "test.sh")], capture_output=True,
                          text=True, env=env, timeout=2400)
    reward = "missing"
    try:
        reward = pathlib.Path("/logs/verifier/reward.txt").read_text().strip()
    except OSError:
        pass
    failed = []
    for line in proc.stdout.split("\n"):
        if line.startswith("FAILED ") and "::" in line:
            failed.append(line.split("::", 1)[1].split()[0].split(" -")[0])
    tail = (proc.stdout.strip().split("\n") or [""])[-1]
    clean()
    return reward, "exit %d; %s" % (proc.returncode, tail[:120]), failed


def main(argv):
    count = int(os.environ.get("TRIAL_COUNT", "30"))
    if os.geteuid() != 0:
        raise SystemExit("this has to run as root: it drops privileges itself")
    mode = argv[0] if argv else "oracle"
    if mode == "oracle":
        r, why, _ = run(str(TASK / "solution"), count)
        print("oracle  reward=%s  %s" % (r, why))
        return 0 if r == "1" else 1
    if mode == "nop":
        r, why, _ = run(None, count)
        print("nop     reward=%s  %s" % (r, why))
        return 0 if r == "0" else 1
    if mode == "--dir":
        r, why, _ = run(argv[1], count)
        print("%-30s reward=%s  %s" % (pathlib.Path(argv[1]).name, r, why))
        return 0
    if mode == "--cheats":
        bad = 0
        for sh in sorted((TASK / "cheat").glob("cheat-*.sh")):
            r, why, _ = run(None, count, script=sh)
            if r != "0":
                bad += 1
            print("%-34s reward=%s%s  %s" % (sh.name, r,
                                             "  <-- SCORED 1" if r != "0" else "", why))
        return 1 if bad else 0
    raise SystemExit("unknown mode %s" % mode)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
