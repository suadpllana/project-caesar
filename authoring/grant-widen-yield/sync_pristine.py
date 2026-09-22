"""Keep tests/pristine in step with the agent-facing tree.

The verifier lays the six submitted files over its own copy of the tree, so that copy has to be
the same tree the agent was given - minus `runs/`, which the verifier never reads because it
generates its own programs, and which is nearly a megabyte of sample input.

    python authoring/grant-widen-yield/sync_pristine.py          copy
    python authoring/grant-widen-yield/sync_pristine.py --check  compare, exit 1 on drift

Run the check after any change under environment/. A stale copy makes the oracle fail inside
the worker with an ImportError, which reads like a broken task rather than a stale mirror.
"""
import filecmp
import pathlib
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
SRC = ROOT / "tasks" / "grant-widen-yield" / "environment" / "app_src"
DST = ROOT / "tasks" / "grant-widen-yield" / "tests" / "pristine"
SKIP = {"runs", "__pycache__"}


def wanted():
    out = []
    for path in sorted(SRC.rglob("*")):
        rel = path.relative_to(SRC)
        if rel.parts[0] in SKIP:
            continue
        if path.is_file():
            out.append(rel)
    return out


def main():
    check = "--check" in sys.argv
    rels = wanted()
    bad = []
    for rel in rels:
        here, there = SRC / rel, DST / rel
        if check:
            if not there.exists() or not filecmp.cmp(here, there, shallow=False):
                bad.append(str(rel))
            continue
        there.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(here, there)
    have = set()
    if DST.exists():
        for path in DST.rglob("*"):
            if path.is_file() and "__pycache__" not in path.parts:
                have.add(path.relative_to(DST))
    extra = sorted(str(r) for r in have - set(rels))
    if check:
        if bad or extra:
            print("pristine is stale")
            for name in bad:
                print("  differs or missing:", name)
            for name in extra:
                print("  not in the agent tree:", name)
            return 1
        print("pristine matches the agent tree (%d files)" % len(rels))
        return 0
    for name in extra:
        (DST / name).unlink()
    print("synced %d files, removed %d" % (len(rels), len(extra)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
