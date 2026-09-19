"""Keep tests/pristine in step with environment/app_src.

The verifier grades by laying the six submitted files over its own copy of the tree, so that
copy has to be the shipped one. A stale copy shows up as an ImportError inside the worker,
which reads like a broken task rather than a copy nobody re-synced.

    python3 sync_pristine.py --check     say whether they agree
    python3 sync_pristine.py             make them agree
"""
from __future__ import annotations

import filecmp
import pathlib
import shutil
import sys

import lab

PRISTINE = lab.TASK / "tests" / "pristine"


def walk(root):
    return sorted(p.relative_to(root) for p in root.rglob("*")
                  if p.is_file() and "__pycache__" not in str(p))


def main(argv):
    if not PRISTINE.exists() and "--check" not in argv:
        shutil.copytree(lab.APP, PRISTINE)
        print("created %s" % PRISTINE)
        return 0
    here, there = walk(lab.APP), walk(PRISTINE)
    same = [p for p in set(here) & set(there) if filecmp.cmp(lab.APP / p, PRISTINE / p, False)]
    drift = sorted((set(here) | set(there)) - set(same))
    for p in drift:
        where = "only in app_src" if p not in there else (
            "only in pristine" if p not in here else "differs")
        print("   %-30s %s" % (str(p), where))
    if not drift:
        print("pristine matches app_src (%d files)" % len(same))
        return 0
    if "--check" in argv:
        print("%d files out of step; run without --check to fix" % len(drift))
        return 1
    shutil.rmtree(PRISTINE)
    shutil.copytree(lab.APP, PRISTINE)
    print("re-synced %d files" % len(walk(PRISTINE)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
