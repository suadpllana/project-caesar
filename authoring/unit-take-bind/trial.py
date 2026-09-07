"""Trial emulation at the container's own absolute paths, for a machine that cannot pull images.

Docker is installed here but the registry blob CDNs are refused by this session's egress policy,
so the two-image runner cannot build. This does the next best thing and runs the shipped
`tests/test.sh` verbatim, at `/tests`, `/work`, `/logs/verifier` and `/app`, with the same
`sandbox` uid the verifier image creates. That means the privilege drop, the root-owned locked
reward channel, the root-only `/tests` and the survivor reap are all really exercised; what is
not exercised is the image build itself and the container's network and mount isolation.

The agent side is emulated the same way: the shipped tree is laid down at `/app`, the solve or
cheat script runs against it, and then only the four declared artifacts are carried over into
the verifier's `/app`, exactly as the harness would.

Usage:
    python3 trial.py oracle | nop | --all
    python3 trial.py --dir <path>      any directory holding step/show/pick/turn.py
    python3 trial.py --cheat <name>    one script from tasks/unit-take-bind/cheat/
"""
import pathlib
import shutil
import subprocess
import sys
import tempfile

import harness

TESTS = harness.TASK / "tests"
CHEATS = harness.TASK / "cheat"
SOLVE = harness.TASK / "solution" / "solve.sh"
VARIANTS = pathlib.Path(__file__).resolve().parent / "variants"
LIVE = (pathlib.Path("/tests"), pathlib.Path("/work"), pathlib.Path("/logs"),
        pathlib.Path("/app"))


def wipe():
    for p in LIVE:
        if p.exists():
            shutil.rmtree(p, ignore_errors=True)


def agent_side(swap, script):
    """Lay the shipped tree at /app, let the submission act on it, keep the four artifacts."""
    wipe()
    shutil.copytree(harness.SRC, "/app")
    if swap is not None:
        for name in harness.PARTS:
            one = pathlib.Path(swap) / name
            if one.is_file():
                shutil.copy(one, pathlib.Path("/app/res") / name)
    log = ""
    if script is not None:
        got = subprocess.run(["bash", str(script)], capture_output=True, text=True, timeout=900)
        log = (got.stdout + got.stderr)[-400:]
        if got.returncode != 0:
            log = "script exit %d: %s" % (got.returncode, log)
    keep = pathlib.Path(tempfile.mkdtemp(prefix="utb-art-"))
    for name in harness.PARTS:
        one = pathlib.Path("/app/res") / name
        if one.is_file():
            shutil.copy(one, keep / name)
    return keep, log


def verifier_side(keep):
    """Materialise only the declared artifacts, then run the shipped test.sh as the harness does."""
    wipe()
    pathlib.Path("/app/res").mkdir(parents=True)
    for name in harness.PARTS:
        one = keep / name
        if one.is_file():
            shutil.copy(one, pathlib.Path("/app/res") / name)
    shutil.copytree(TESTS, "/tests", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    pathlib.Path("/tests/test.sh").chmod(0o755)
    pathlib.Path("/logs/verifier").mkdir(parents=True)
    got = subprocess.run(["bash", "/tests/test.sh"], capture_output=True, text=True, timeout=1800)
    reward = pathlib.Path("/logs/verifier/reward.txt")
    score = reward.read_text(encoding="utf-8").strip() if reward.is_file() else "missing"
    whole = got.stdout + got.stderr
    tail = [ln for ln in whole.splitlines() if ln.strip()][-2:]
    wipe()
    return score, " / ".join(tail), whole


def one(label, swap=None, script=None, want_log=False):
    keep, log = agent_side(swap, script)
    score, tail, whole = verifier_side(keep)
    shutil.rmtree(keep, ignore_errors=True)
    print("%-40s reward %s   %s" % (label, score, tail if score != "1" else ""), flush=True)
    if log.startswith("script exit"):
        print("    agent side: %s" % log.replace("\n", " ")[:200], flush=True)
    return (score, whole) if want_log else score


def main():
    args = sys.argv[1:]
    if args and args[0] == "oracle":
        return 0 if one("oracle", None, SOLVE) == "1" else 1
    if args and args[0] == "nop":
        return 0 if one("nop") == "0" else 1
    if args and args[0] == "--dir":
        return 0 if one(args[1], pathlib.Path(args[1])) == "1" else 1
    if args and args[0] == "--cheat":
        return 0 if one("cheat:" + args[1], None, CHEATS / args[1]) == "0" else 1
    if args and args[0] == "--all":
        bad = 0
        bad += one("oracle", None, SOLVE) != "1"
        bad += one("nop") != "0"
        if VARIANTS.is_dir():
            for d in sorted(p for p in VARIANTS.iterdir() if p.is_dir()):
                bad += one("variant:" + d.name, d) != "1"
        if CHEATS.is_dir():
            for script in sorted(CHEATS.glob("cheat-*.sh")):
                bad += one("cheat:" + script.stem[6:], None, script) != "0"
        print("\n%s" % ("every row as expected" if not bad else "%d row(s) wrong" % bad))
        return 1 if bad else 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
