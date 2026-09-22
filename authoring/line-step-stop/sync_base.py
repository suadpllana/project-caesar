"""Copy the agent-facing tgt/ and dbg/ packages into tests/base/, the verifier's pristine tree.

    python sync_base.py          write
    python sync_base.py --check  fail if tests/base differs from environment/app_src

The verifier lays the three submitted files over this copy, so every other module the
debugger imports is the one shipped in the environment. Run --check after any change to
environment/: a stale copy makes the oracle fail with an import error that reads like a
broken task (CLAUDE.md, publish-settle-order).
"""
import filecmp
import os
import shutil
import sys

from lab import APP, TASK

BASE = os.path.normpath(os.path.join(TASK, "tests", "base"))
PKGS = ("tgt", "dbg")


def files(root):
    out = set()
    for pkg in PKGS:
        for d, _, fs in os.walk(os.path.join(root, pkg)):
            if "__pycache__" in d:
                continue
            for f in fs:
                out.add(os.path.relpath(os.path.join(d, f), root))
    return out


def check():
    a, b = files(APP), files(BASE)
    bad = sorted(a ^ b)
    for f in sorted(a & b):
        if not filecmp.cmp(os.path.join(APP, f), os.path.join(BASE, f), shallow=False):
            bad.append(f)
    return bad


if __name__ == "__main__":
    if "--check" in sys.argv:
        bad = check()
        print("tests/base in sync" if not bad else "OUT OF SYNC: %s" % bad)
        sys.exit(1 if bad else 0)
    if os.path.exists(BASE):
        shutil.rmtree(BASE)
    for pkg in PKGS:
        shutil.copytree(os.path.join(APP, pkg), os.path.join(BASE, pkg),
                        ignore=shutil.ignore_patterns("__pycache__"))
    print("synced", sorted(files(BASE)))
