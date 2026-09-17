"""Keep tests/pristine/ in step with environment/app_src/.

The verifier lays the six submitted files over its own copy of the tree, so that copy has to
be the tree that shipped. It is a copy, and copies go stale: rebuilding the environment
without re-syncing makes the oracle fail inside the worker with an import error, which reads
like a broken task rather than a stale mirror.

    python3 sync.py            copy environment/app_src -> tests/pristine
    python3 sync.py --check    exit 1 if they differ
"""
import filecmp
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
TASK = ROOT / "tasks" / "still-graft-charge"
SRC = TASK / "environment" / "app_src"
DST = TASK / "tests" / "pristine"
SKIP = {"progs", "__pycache__"}


def wanted():
    out = []
    for path in sorted(SRC.rglob("*")):
        rel = path.relative_to(SRC)
        if set(rel.parts) & SKIP or not path.is_file():
            continue
        out.append(rel)
    return out


def main():
    check = "--check" in sys.argv
    bad = []
    keep = set()
    for rel in wanted():
        keep.add(rel)
        there = DST / rel
        if not there.is_file() or not filecmp.cmp(SRC / rel, there, shallow=False):
            bad.append(str(rel))
            if not check:
                there.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(SRC / rel, there)
    for path in sorted(DST.rglob("*")):
        if path.is_file() and path.relative_to(DST) not in keep:
            bad.append("extra: %s" % path.relative_to(DST))
            if not check:
                path.unlink()
    if check and bad:
        print("pristine is stale: %s" % ", ".join(bad))
        return 1
    print("%d files, %d %s" % (len(keep), len(bad), "stale" if check else "updated"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
