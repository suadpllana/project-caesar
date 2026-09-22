"""Keep tests/pristine in step with the shipped tree.

The verifier lays the six submitted files over its own copy of the tree, so that copy has to
be the shipped one. It goes stale silently when the environment is rebuilt, and a stale copy
fails inside the worker in a way that reads like a broken task.

The sample programs are left out on purpose: they are a megabyte and a half that the worker
never opens, because it builds its own programs.

    python sync_pristine.py            copy
    python sync_pristine.py --check    fail when they differ
"""
import filecmp
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TASK = HERE.parent.parent / "tasks" / "pin-drift-redo"
SRC = TASK / "environment" / "app_src"
DST = TASK / "tests" / "pristine"
SKIP = {"plans"}


def wanted():
    for p in sorted(SRC.rglob("*")):
        rel = p.relative_to(SRC)
        if rel.parts[0] in SKIP or "__pycache__" in rel.parts:
            continue
        if p.is_file():
            yield rel


def main():
    check = "--check" in sys.argv
    bad = []
    for rel in wanted():
        src, dst = SRC / rel, DST / rel
        if check:
            if not dst.is_file() or not filecmp.cmp(src, dst, shallow=False):
                bad.append(str(rel))
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
    if not check:
        for p in sorted(DST.rglob("*")):
            rel = p.relative_to(DST)
            if p.is_file() and rel not in set(wanted()):
                p.unlink()
                print("removed stale %s" % rel)
    if check:
        extra = [str(p.relative_to(DST)) for p in DST.rglob("*")
                 if p.is_file() and p.relative_to(DST) not in set(wanted())]
        if bad or extra:
            raise SystemExit("pristine is stale: differs %s, extra %s" % (bad, extra))
        print("pristine matches the shipped tree (%d files)" % len(list(wanted())))
    else:
        print("synced %d files into tests/pristine" % len(list(wanted())))


if __name__ == "__main__":
    main()
