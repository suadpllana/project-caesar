#!/usr/bin/env python3
"""Print every enumerated case under a module set and check it against the sealed model.

    python3 -u authoring/page-pass-owe/hand.py solution
    python3 -u authoring/page-pass-owe/hand.py environment/app_src/lst
    python3 -u authoring/page-pass-owe/hand.py solution --only order-tie
"""
import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
TASK = ROOT / "tasks" / "page-pass-owe"
PARTS = ("seq", "scr", "owe", "pg", "edt", "rep")

CHILD = '''
import sys
sys.path.insert(0, TREE)
sys.path.insert(0, TESTS)
sys.path.insert(0, SEAL)
import cases, model, run_lst
bad = 0
for name in cases.ORDER:
    if ONLY and name != ONLY:
        continue
    text = "\\n".join(cases.prog(name)) + "\\n"
    want = model.run(text)
    try:
        got = run_lst.run(text)
    except Exception as exc:
        got = ["!! " + repr(exc)]
    print(name)
    for line in got:
        print("   " + line)
    if got != want:
        bad += 1
        print("   MODEL WANTS:")
        for line in want:
            print("      " + line)
print("mismatches: " + str(bad))
'''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("modules")
    ap.add_argument("--only", default="")
    args = ap.parse_args()
    src = Path(args.modules)
    if not src.is_absolute():
        src = ROOT / args.modules if (ROOT / args.modules).is_dir() else TASK / args.modules
    tmp = Path(tempfile.mkdtemp(prefix="ppo-h-"))
    shutil.copytree(TASK / "environment" / "app_src", tmp / "app")
    for part in PARTS:
        shutil.copyfile(src / (part + ".py"), tmp / "app" / "lst" / (part + ".py"))
    head = "TREE = %r\nTESTS = %r\nSEAL = %r\nONLY = %r\n" % (
        str(tmp / "app"), str(TASK / "tests"), str(TASK / "tests" / "seal"), args.only)
    done = subprocess.run([sys.executable, "-u", "-c", head + CHILD],
                          capture_output=True, text=True)
    shutil.rmtree(tmp, ignore_errors=True)
    sys.stdout.write(done.stdout)
    sys.stderr.write(done.stderr)
    return done.returncode


if __name__ == "__main__":
    sys.exit(main())
