#!/usr/bin/env python3
"""Keep tests/pristine/ in step with environment/app_src/.

The verifier grades the submitted opt files laid over its own copy of the tree, so that copy
has to be the shipped one. `--check` reports drift without writing, and is run after every
change to environment/.
"""
import filecmp
import pathlib
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
TASK = ROOT / "tasks" / "shard-spend-carry"
SRC = TASK / "environment" / "app_src"
DST = TASK / "tests" / "pristine"
SKIP = {"progs"}


def walk(root):
    return sorted(
        p.relative_to(root)
        for p in root.rglob("*")
        if p.is_file() and "__pycache__" not in p.parts
        and p.relative_to(root).parts[0] not in SKIP
    )


def main():
    check = "--check" in sys.argv[1:]
    want = walk(SRC)
    if not check:
        if DST.exists():
            shutil.rmtree(DST)
        for rel in want:
            out = DST / rel
            out.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(SRC / rel, out)
        print("synced %d files into %s" % (len(want), DST))
        return 0
    have = walk(DST) if DST.exists() else []
    bad = [str(r) for r in set(want) ^ set(have)]
    for rel in want:
        if rel in have and not filecmp.cmp(SRC / rel, DST / rel, shallow=False):
            bad.append(str(rel))
    if bad:
        print("pristine is stale: %s" % sorted(bad))
        return 1
    print("pristine matches environment/app_src (%d files)" % len(want))
    return 0


if __name__ == "__main__":
    sys.exit(main())
