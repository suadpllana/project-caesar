"""Keep tests/pristine/ identical to environment/app_src/.

`tests/pristine/` is the copy the verifier lays the submitted files over, so a stale copy
makes the oracle fail inside the worker with an import error that reads like a broken task
rather than a stale mirror (CLAUDE.md, publish-settle-order). Run this after any change to
the environment, and `--check` before any gate.

Usage:
    python authoring/pull-check-stale/sync_pristine.py [--check]
"""

import filecmp
import shutil
import sys
from pathlib import Path

TASK = Path(__file__).resolve().parent.parent.parent / "tasks" / "pull-check-stale"
SRC = TASK / "environment" / "app_src"
DST = TASK / "tests" / "pristine"


SKIP = ("__pycache__",)


def walk(root):
    """Every file that belongs to the tree. Bytecode caches are not part of it: running the
    shipped service inside environment/app_src leaves them behind, and a stale one in the
    mirror is a difference this script would otherwise report forever."""
    return sorted(p.relative_to(root) for p in root.rglob("*")
                  if p.is_file() and p.suffix != ".pyc"
                  and not any(part in SKIP for part in p.parts))


def main(argv):
    check = "--check" in argv
    want = walk(SRC)
    if not DST.is_dir():
        if check:
            print("tests/pristine/ does not exist")
            return 1
        shutil.copytree(SRC, DST)
        print("created tests/pristine with %d files" % len(want))
        return 0
    have = walk(DST)
    bad = [str(p) for p in set(want) ^ set(have)]
    for rel in sorted(set(want) & set(have)):
        if not filecmp.cmp(SRC / rel, DST / rel, shallow=False):
            bad.append(str(rel))
    if check:
        if bad:
            print("tests/pristine is stale: %s" % ", ".join(sorted(bad)))
            return 1
        print("tests/pristine matches environment/app_src (%d files)" % len(want))
        return 0
    shutil.rmtree(DST)
    shutil.copytree(SRC, DST)
    print("synced %d files into tests/pristine" % len(want))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
