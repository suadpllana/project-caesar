"""Assert the layer, not the reward: prove each isolation rule actually denies what it claims.

Every reward-tamper cheat scores 0, but a cheat can score 0 because the engine it shipped was
wrong and never because the attack was blocked. This sets up the verifier's own layout exactly
as `tests/test.sh` does, then, as the sandbox uid, tries each thing a submission would try and
requires it to be refused. It also proves `reap.py` reaches a double-forked survivor, which is
the one thing a process-group kill would miss.

Usage:
    python3 probecheck.py
"""
import pathlib
import shutil
import subprocess
import sys
import time

import harness

TESTS = harness.TASK / "tests"
SANDBOX = "1002"
LIVE = (pathlib.Path("/tests"), pathlib.Path("/logs"), pathlib.Path("/work"))


def wipe():
    for p in LIVE:
        if p.exists():
            shutil.rmtree(p, ignore_errors=True)


def as_sandbox(code, timeout=30):
    return subprocess.run(
        ["setpriv", "--reuid=" + SANDBOX, "--regid=" + SANDBOX, "--clear-groups",
         sys.executable, "-c", code],
        capture_output=True, text=True, timeout=timeout)


def layout():
    """What test.sh has built by the time the worker starts."""
    wipe()
    shutil.copytree(TESTS, "/tests", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    logs = pathlib.Path("/logs/verifier")
    logs.mkdir(parents=True)
    logs.chmod(0o700)
    (logs / "reward.txt").write_text("0\n", encoding="utf-8")
    (logs / "nonce").write_text("0" * 32 + "\n", encoding="utf-8")
    work = pathlib.Path("/work")
    work.mkdir()
    subprocess.run(["chown", "-R", "sandbox:sandbox", "/work"], check=True)
    pathlib.Path("/tests").chmod(0o700)


DENIALS = (
    ("read the frozen answers", "open('/tests/gt.json').read()"),
    ("read the sealed model", "open('/tests/model.py').read()"),
    ("read the generator", "open('/tests/gen.py').read()"),
    ("list the verifier", "import os; os.listdir('/tests')"),
    ("read the nonce", "open('/logs/verifier/nonce').read()"),
    ("write the reward", "open('/logs/verifier/reward.txt','w').write('1')"),
    ("list the reward channel", "import os; os.listdir('/logs/verifier')"),
    ("open the reward channel", "import os; os.chmod('/logs/verifier', 0o777)"),
    ("import the sealed model", "import sys; sys.path.insert(0,'/tests'); import model"),
)

SURVIVOR = (
    "import os, time\n"
    "if os.fork() == 0:\n"
    "    os.setsid()\n"
    "    if os.fork() == 0:\n"
    "        null = os.open('/dev/null', os.O_RDWR)\n"
    "        for fd in (0, 1, 2):\n"
    "            os.dup2(null, fd)\n"
    "        open('/work/alive', 'w').write(str(os.getpid()))\n"
    "        time.sleep(120)\n"
    "    os._exit(0)\n"
    "else:\n"
    "    os.wait()\n"
)


def running(pid):
    """Alive and not a zombie. Without an init that reaps, a killed pid keeps its /proc entry."""
    if pid is None:
        return False
    try:
        status = pathlib.Path("/proc/%d/status" % pid).read_text(encoding="utf-8")
    except OSError:
        return False
    for line in status.splitlines():
        if line.startswith("State:"):
            return not line.split()[1].startswith("Z")
    return True


def main():
    layout()
    bad = []
    print("uid 1002, with the layout test.sh builds:", flush=True)
    for label, code in DENIALS:
        got = as_sandbox(code)
        ok = got.returncode != 0
        print("   %-26s %s" % (label, "denied" if ok else "ALLOWED"), flush=True)
        if not ok:
            bad.append(label)

    # A double fork escapes the process group; only the by-owner sweep in reap.py reaches it.
    as_sandbox(SURVIVOR, timeout=60)
    time.sleep(1)
    alive = pathlib.Path("/work/alive")
    pid = int(alive.read_text(encoding="utf-8").strip()) if alive.is_file() else None
    before = running(pid)
    reaped = subprocess.run([sys.executable, "/tests/reap.py"], capture_output=True, text=True)
    time.sleep(1)
    after = running(pid)
    print("   %-26s %s (%s)" % ("double-forked survivor",
                                "reaped" if before and not after else "NOT REAPED",
                                reaped.stdout.strip()), flush=True)
    if not before:
        bad.append("survivor never started - the probe proved nothing")
    elif after:
        bad.append("survivor outlived reap.py")

    wipe()
    if bad:
        print("\nFAIL: %s" % "; ".join(bad))
        return 1
    print("\nevery attempt refused, and the survivor was reaped")
    return 0


if __name__ == "__main__":
    sys.exit(main())
