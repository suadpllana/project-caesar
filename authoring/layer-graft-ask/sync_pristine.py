"""Keep tests/pristine in step with environment/app_src.

The verifier stages its own copy of the tree and lays the six submitted files over it, so a
stale copy makes the oracle fail inside the worker with an import error, which reads like a
broken task rather than a mirror nobody re-synced. `--check` reports drift without writing.
"""
import filecmp
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
TASK = ROOT / "tasks" / "layer-graft-ask"
SRC = TASK / "environment" / "app_src"
DST = TASK / "tests" / "pristine"
SKIP = {"plans"}


def walk(base):
    out = []
    for path in sorted(base.rglob("*")):
        rel = path.relative_to(base)
        if rel.parts and rel.parts[0] in SKIP:
            continue
        if path.is_file() and "__pycache__" not in str(rel):
            out.append(rel)
    return out


def main(argv):
    check = "--check" in argv
    want = walk(SRC)
    have = walk(DST) if DST.exists() else []
    drift = []
    for rel in want:
        target = DST / rel
        if not target.exists() or not filecmp.cmp(SRC / rel, target, shallow=False):
            drift.append(str(rel))
    for rel in have:
        if rel not in want:
            drift.append("extra: %s" % rel)
    if check:
        for item in drift:
            print("drift %s" % item)
        print("%d files, %d drifted" % (len(want), len(drift)))
        return 1 if drift else 0
    if DST.exists():
        shutil.rmtree(DST)
    for rel in want:
        (DST / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(SRC / rel, DST / rel)
    print("synced %d files into %s" % (len(want), DST))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
