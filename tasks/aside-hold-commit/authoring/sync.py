"""Refresh tests/pristine from environment/app_src. The grader compares against it."""
import os
import shutil

import stage

DEST = os.path.join(stage.TESTS, "pristine")


def main():
    if os.path.isdir(DEST):
        shutil.rmtree(DEST)
    shutil.copytree(stage.APP, DEST, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    n = sum(len(f) for _, _, f in os.walk(DEST))
    print("pristine refreshed: %d files" % n)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
