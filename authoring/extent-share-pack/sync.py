"""Keep tests/pristine in step with environment/app_src, or say where they differ.

The verifier lays the six submitted files over its own copy of the tree, so that copy has to be
the tree that shipped. A stale mirror shows up as an ImportError inside the worker, which reads
like a broken task rather than a copy nobody re-synced.

    python sync.py            copy environment/app_src over tests/pristine
    python sync.py --check    exit 1 if they differ, listing the files
"""
import filecmp
import pathlib
import shutil
import sys

TASK = pathlib.Path(__file__).resolve().parent.parent.parent / "tasks" / "extent-share-pack"
SRC = TASK / "environment" / "app_src"
DST = TASK / "tests" / "pristine"
SKIP = {"progs", "__pycache__"}


def walk(root):
    for p in sorted(root.rglob("*")):
        if p.is_file() and not any(part in SKIP for part in p.relative_to(root).parts):
            yield p.relative_to(root)


def main():
    check = "--check" in sys.argv
    want = list(walk(SRC))
    have = list(walk(DST)) if DST.exists() else []
    bad = []
    for rel in want:
        a, b = SRC / rel, DST / rel
        if not b.exists() or not filecmp.cmp(a, b, shallow=False):
            bad.append(str(rel))
            if not check:
                b.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(a, b)
    for rel in have:
        if rel not in want:
            bad.append("extra: %s" % rel)
            if not check:
                (DST / rel).unlink()
    if check:
        if bad:
            print("pristine differs from environment/app_src:")
            for one in bad:
                print("   " + one)
            return 1
        print("pristine matches environment/app_src (%d files)" % len(want))
        return 0
    print("synced %d file(s); pristine now holds %d" % (len(bad), len(want)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
