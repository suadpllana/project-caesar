"""Keep tests/pristine an exact mirror of the shipped tree.

The verifier stages its own copy of the tree and lays the submitted files over it, so a
pristine copy that has drifted from what the agent was given grades a different program.
"""
import filecmp
import pathlib
import shutil
import sys

TASK = pathlib.Path(__file__).resolve().parents[2] / "tasks" / "publish-settle-order"
SRC = TASK / "environment" / "app_src"
DST = TASK / "tests" / "pristine"


def diff(a, b):
    cmp = filecmp.dircmp(str(a), str(b))
    bad = list(cmp.left_only) + list(cmp.right_only) + list(cmp.diff_files)
    for sub in cmp.common_dirs:
        bad += ["%s/%s" % (sub, x) for x in diff(a / sub, b / sub)]
    return bad


def main():
    if "--check" not in sys.argv:
        if DST.exists():
            shutil.rmtree(DST)
        shutil.copytree(SRC, DST, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    bad = diff(SRC, DST)
    if bad:
        raise SystemExit("pristine has drifted: %s" % ", ".join(sorted(bad)))
    print("pristine mirrors the shipped tree")


if __name__ == "__main__":
    main()
