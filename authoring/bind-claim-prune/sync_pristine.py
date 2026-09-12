"""Keep tests/pristine in step with environment/app_src, and say so when it is not.

The overlay the worker stages is a copy, and a copy goes stale the moment the tree is rebuilt:
the failure that follows is an ImportError inside the verifier, which reads like a broken task
rather than a stale mirror. Run this with --check after any change under environment/.

    python authoring/bind-claim-prune/sync_pristine.py [--check]
"""
import filecmp
import pathlib
import shutil
import sys

HERE = pathlib.Path(__file__).resolve().parent
TASK = HERE.parent.parent / "tasks" / "bind-claim-prune"
SRC = TASK / "environment" / "app_src"
DST = TASK / "tests" / "pristine"
SKIP = {"__pycache__"}


def walk(root):
    out = {}
    for p in sorted(root.rglob("*")):
        if p.is_dir() or any(part in SKIP for part in p.parts):
            continue
        out[str(p.relative_to(root))] = p
    return out


def main():
    check = "--check" in sys.argv
    src, dst = walk(SRC), walk(DST)
    off = []
    for rel in sorted(set(src) | set(dst)):
        if rel not in src:
            off.append(("extra", rel))
        elif rel not in dst:
            off.append(("missing", rel))
        elif not filecmp.cmp(src[rel], dst[rel], shallow=False):
            off.append(("differs", rel))
    for why, rel in off:
        print("%-8s %s" % (why, rel))
    if not off:
        print("pristine is in step with app_src (%d files)" % len(src))
        return 0
    if check:
        print("%d out of step - run without --check to re-sync" % len(off))
        return 1
    if DST.exists():
        shutil.rmtree(DST)
    shutil.copytree(SRC, DST, ignore=shutil.ignore_patterns(*SKIP))
    print("re-synced %d files" % len(walk(DST)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
