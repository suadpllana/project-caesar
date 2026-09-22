"""Keep tests/pristine in step with environment/app_src. A stale copy makes the oracle fail
with an import error inside the worker, which reads like a broken task rather than a mirror
that was never re-synced."""
import filecmp
import shutil
import sys
from pathlib import Path

T = Path("/home/user/project-caesar/tasks/rekey-copy-replay")
SRC = T / "environment" / "app_src"
DST = T / "tests" / "pristine"


SKIP = ("__pycache__", "progs")


def listing(root):
    out = []
    for p in root.rglob("*"):
        rel = str(p.relative_to(root))
        if not p.is_file() or any(part in rel.split("/") for part in SKIP):
            continue
        out.append(rel)
    return sorted(out)


def main():
    check = "--check" in sys.argv
    if check:
        if not DST.is_dir():
            print("pristine missing")
            return 1
        a, b = listing(SRC), listing(DST)
        if a != b:
            print("file lists differ: only in app_src %s, only in pristine %s"
                  % (sorted(set(a) - set(b)), sorted(set(b) - set(a))))
            return 1
        bad = [n for n in a if not filecmp.cmp(SRC / n, DST / n, shallow=False)]
        if bad:
            print("contents differ: %s" % bad)
            return 1
        print("pristine matches app_src (%d files)" % len(a))
        return 0
    if DST.is_dir():
        shutil.rmtree(DST)
    shutil.copytree(SRC, DST, ignore=shutil.ignore_patterns(*SKIP))
    print("synced %d files" % len(listing(DST)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
