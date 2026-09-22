"""Mirror environment/app_src into tests/pristine. Authoring only.

    python sync_pristine.py          copy
    python sync_pristine.py --check  exit 1 when the mirror differs from the environment

The worker stages the pristine copy and lays the five submitted files over it, so a stale
mirror grades the agent against a tree the agent never saw.
"""
import filecmp
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.join(HERE, "..", "..", "tasks", "partial-key-purge")
SRC = os.path.join(TASK, "environment", "app_src")
DST = os.path.join(TASK, "tests", "pristine")


def listing(root):
    out = set()
    for base, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for f in files:
            if not f.endswith(".pyc"):
                out.add(os.path.relpath(os.path.join(base, f), root))
    return out


def differs():
    a, b = listing(SRC), listing(DST) if os.path.isdir(DST) else set()
    if a != b:
        return sorted(a ^ b)
    return [f for f in sorted(a) if not filecmp.cmp(os.path.join(SRC, f), os.path.join(DST, f), False)]


def main():
    if "--check" in sys.argv:
        bad = differs()
        print("pristine in sync" if not bad else "pristine differs: %s" % bad[:5])
        return 1 if bad else 0
    if os.path.isdir(DST):
        shutil.rmtree(DST)
    shutil.copytree(SRC, DST, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    print("synced", len(listing(DST)), "files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
