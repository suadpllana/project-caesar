"""Run the cheat suite and report which assertion caught each one.

A cheat that scores 0 by dying on an import error has been rejected by nothing, so this
records the test that failed rather than the reward, and fails loudly on any cheat that
either passes or is caught only by the report failing to load when it was aimed at a rule.

This is the host emulation. It does not exercise the container isolation - the privilege
drop, the root-owned reward channel, the root-only ground truth - so the reward-tamper
probes are re-run under tools/docker_trial.py, where those exist.
"""

import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.normpath(os.path.join(HERE, "..", "..", "tasks", "slice-trip-fill"))
TESTS = os.path.join(TASK, "tests")
PRISTINE = os.path.join(TESTS, "pristine")
CHEATS = os.path.join(TASK, "cheat")

FAILED = re.compile(r"^FAILED .*::(\w+)", re.M)


def one(path, small, deep, nonce):
    root = tempfile.mkdtemp(prefix="stf-cheat-")
    app = os.path.join(root, "app")
    shutil.copytree(PRISTINE, app)
    env = dict(os.environ, APP=app)
    r = subprocess.run(["bash", path], env=env, capture_output=True, text=True)
    if r.returncode:
        shutil.rmtree(root, ignore_errors=True)
        return ["cheat script itself failed: %s" % r.stderr.strip()[-200:]]
    out = os.path.join(root, "out.json")
    env.update(APPDIR=app, RUN_NONCE=nonce, RUN_SMALL=str(small), RUN_DEEP=str(deep),
               PYTHONDONTWRITEBYTECODE="1")
    subprocess.run([sys.executable, os.path.join(TESTS, "runner.py"), out],
                   env=env, capture_output=True, text=True, timeout=900)
    env.update(RUN_OUT=out, APP_DIR=app, PRISTINE_DIR=PRISTINE, PYTHONPATH=TESTS)
    g = subprocess.run([sys.executable, "-m", "pytest", "-q",
                        os.path.join(TESTS, "test_outputs.py"), "-rf"],
                       env=env, capture_output=True, text=True, timeout=900)
    shutil.rmtree(root, ignore_errors=True)
    if g.returncode == 0:
        return []
    hits = sorted(set(FAILED.findall(g.stdout)))
    if not hits:
        head = (g.stdout + g.stderr).strip().splitlines()
        return ["collection error: %s" % (head[-1] if head else "unknown")]
    return hits


def main(argv):
    small = int(argv[1]) if len(argv) > 1 else 60
    deep = int(argv[2]) if len(argv) > 2 else 1
    names = sorted(n for n in os.listdir(CHEATS)
                   if n.startswith("cheat-") and n.endswith(".sh"))
    bad = []
    for name in names:
        hits = one(os.path.join(CHEATS, name), small, deep, "cheat-report")
        label = name[len("cheat-"):-len(".sh")]
        if not hits:
            print("%-22s SCORED 1 - verifier defect" % label, flush=True)
            bad.append(label)
        else:
            print("%-22s 0  caught by %s" % (label, ", ".join(hits)), flush=True)
    print()
    if bad:
        print("%d cheats scored 1: %s" % (len(bad), bad))
        return 1
    print("all %d cheats scored 0" % len(names))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
