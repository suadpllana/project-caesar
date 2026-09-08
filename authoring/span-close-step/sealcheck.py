"""Can the sandbox uid reach the answers? Asked with real permission bits.

The verifier executes agent code in a process that has `/tests` on its import path,
so the seal is the thing standing between submitted code and the sealed model. A
container would show this; no container can be built in this workspace, so this
shows the half that does not need one: stage the verifier's `tests/` under a
world-traversable path, apply exactly the mode changes `tests/Dockerfile` applies,
drop to the sandbox uid with `setpriv`, and report what is reachable from there.

What it does not show is the rest of the isolation - the locked reward channel, the
survivor sweep, the privileged grader - which needs the two-container runner.

    sudo python3 authoring/span-close-step/sealcheck.py
"""
import os
import pathlib
import shutil
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
TESTS = ROOT / "tasks" / "span-close-step" / "tests"
STAGE = pathlib.Path("/opt/scs-sealcheck")
SANDBOX = 1002

PROBE = r"""
import os
import sys

sys.path.insert(0, "%(stage)s/tests/seal")
sys.path.insert(0, "%(stage)s/tests")

WANT_BLOCKED = ("import model", "import gen", "import cases", "read gt.json", "list seal")
CHECKS = (
    ("import model", lambda: __import__("model")),
    ("import gen", lambda: __import__("gen")),
    ("import cases", lambda: __import__("cases")),
    ("read gt.json", lambda: open("%(stage)s/tests/seal/gt.json").read()),
    ("list seal", lambda: os.listdir("%(stage)s/tests/seal")),
    ("read worker.py", lambda: open("%(stage)s/tests/worker.py").read()),
    ("read pristine", lambda: open("%(stage)s/tests/pristine/train/ops.py").read()),
)

bad = 0
print("   running as uid %%d" %% os.getuid())
for name, fn in CHECKS:
    try:
        fn()
        got = "reachable"
    except Exception as exc:
        got = "blocked (%%s)" %% type(exc).__name__
    want_block = name in WANT_BLOCKED
    ok = want_block == got.startswith("blocked")
    bad += 0 if ok else 1
    print("   %%-16s %%-22s %%s" %% (name, got, "ok" if ok else "WRONG SIDE OF THE SEAL"))
sys.exit(1 if bad else 0)
"""


def main():
    if os.geteuid() != 0:
        print("needs root: the point is to drop from root to the sandbox uid")
        return 2
    if STAGE.exists():
        shutil.rmtree(STAGE)
    STAGE.mkdir(parents=True)
    shutil.copytree(TESTS, STAGE / "tests")
    try:
        # Exactly what tests/Dockerfile does, and nothing else.
        subprocess.run(["chmod", "-R", "a+rX", str(STAGE)], check=True)
        subprocess.run(["chown", "-R", "root:root", str(STAGE / "tests" / "seal")], check=True)
        subprocess.run(["chmod", "700", str(STAGE / "tests" / "seal")], check=True)
        for f in sorted((STAGE / "tests" / "seal").iterdir()):
            f.chmod(0o600)
        print("== span-close-step seal, under the image's own mode bits")
        proc = subprocess.run(
            ["setpriv", "--reuid=%d" % SANDBOX, "--regid=%d" % SANDBOX, "--clear-groups",
             sys.executable, "-c", PROBE % {"stage": STAGE}])
        return proc.returncode
    finally:
        shutil.rmtree(STAGE, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
