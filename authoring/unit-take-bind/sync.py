"""Keep tests/pristine a byte copy of environment/app_src, and rebuild nothing else.

The verifier overlays the four submitted files onto its own copy of the tree, so the copy has
to match what shipped. Run after any change under environment/app_src/.
"""
import filecmp
import pathlib
import shutil
import sys

import harness

DST = harness.TASK / "tests" / "pristine"


def main():
    if DST.exists():
        shutil.rmtree(DST)
    shutil.copytree(harness.SRC, DST, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    diff = filecmp.dircmp(harness.SRC, DST)
    bad = list(diff.left_only) + list(diff.right_only) + list(diff.diff_files)
    print("pristine synced from app_src; differences: %s" % (bad or "none"), flush=True)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
