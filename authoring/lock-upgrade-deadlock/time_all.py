"""Time the worker over the whole graded set for the reference and the readings that are
right and only slow, each under a cap, the way the execution limit sees them.

    python3 authoring/lock-upgrade-deadlock/time_all.py [--cap SECONDS] [name ...]

`reference` is solution/, `variants/<name>` is one of the correct variants beside this
script, and any other name is a cheat under cheat/ whose five files are installed over the
shipped tree. The population is the verifier's own generator with the
shipped sizes and a fixed seed.
"""
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import time

HERE = pathlib.Path(__file__).resolve().parent
TASK = HERE.parents[1] / "tasks" / "lock-upgrade-deadlock"
BLOCK = re.compile(r"cat > /app/hold/(\w+\.py) <<'PYEOF'\n(.*?)\nPYEOF\n", re.S)
PARTS = ("mark.py", "item.py", "wait.py", "cyc.py", "txn.py")


def policy_of(name):
    d = pathlib.Path(tempfile.mkdtemp(prefix="crc-time-"))
    if name == "reference":
        for part in PARTS:
            shutil.copy(TASK / "solution" / part, d / part)
    elif name.startswith("variants/"):
        for part in PARTS:
            shutil.copy(HERE / name / part, d / part)
    else:
        text = (TASK / "cheat" / ("cheat-%s.sh" % name)).read_text()
        for fn, src in BLOCK.findall(text):
            (d / fn).write_text(src + "\n")
    return d


def main(argv):
    cap = 300
    if "--cap" in argv:
        i = argv.index("--cap")
        cap = int(argv[i + 1])
        del argv[i:i + 2]
    names = argv or ["reference", "all-live", "per-participant", "candidate-verify",
                     "whole-rebuild"]
    for name in names:
        work = pathlib.Path(tempfile.mkdtemp(prefix="crc-work-"))
        (work / "nonce").write_text("timing-seed\n")
        (work / "per").write_text("40\n")
        (work / "heavy").write_text("6\n")
        env = dict(os.environ, CRC_TESTS=str(TASK / "tests"), CRC_WORK=str(work),
                   CRC_SUB=str(policy_of(name)))
        t0 = time.time()
        try:
            proc = subprocess.run([sys.executable, str(TASK / "tests" / "worker.py"), "--out",
                                   str(work / "out.json")], env=env, capture_output=True,
                                  text=True, timeout=cap)
            took = time.time() - t0
            print("%-18s %7.1fs  exit %d" % (name, took, proc.returncode), flush=True)
        except subprocess.TimeoutExpired:
            print("%-18s   >%ds  (cut off)" % (name, cap), flush=True)
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    main(sys.argv[1:])
