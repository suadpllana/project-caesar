"""Keep tests/pristine/ a true mirror of environment/app_src/, and say when it is not.

A copy goes stale, and a stale mirror fails the oracle with an ImportError inside the worker,
which reads like a broken task rather than a copy nobody re-synced (CLAUDE.md, 2026-09-08).
Also keeps tests/seal/spec.py identical to the shipped parser, since the model parses with it.

    python sync_pristine.py            copy
    python sync_pristine.py --check    compare, exit 1 on any difference
"""
import filecmp
import pathlib
import shutil
import sys

HERE = pathlib.Path(__file__).resolve().parent
TASK = HERE.parent.parent / "tasks" / "trail-credit-void"
SRC = TASK / "environment" / "app_src"
DST = TASK / "tests" / "pristine"
SEAL_SPEC = TASK / "tests" / "seal" / "spec.py"


def walk(root):
    return sorted(p.relative_to(root) for p in root.rglob("*") if p.is_file())


def check():
    bad = []
    here, there = walk(SRC), walk(DST)
    for rel in sorted(set(here) | set(there)):
        if rel not in here:
            bad.append("only in pristine: %s" % rel)
        elif rel not in there:
            bad.append("missing from pristine: %s" % rel)
        elif not filecmp.cmp(SRC / rel, DST / rel, shallow=False):
            bad.append("differs: %s" % rel)
    if not filecmp.cmp(SRC / "crd" / "spec.py", SEAL_SPEC, shallow=False):
        bad.append("differs: tests/seal/spec.py against the shipped parser")
    for line in bad:
        print(line)
    print("pristine %s" % ("stale" if bad else "matches app_src"))
    return 1 if bad else 0


def copy():
    if DST.exists():
        shutil.rmtree(DST)
    shutil.copytree(SRC, DST)
    shutil.copyfile(SRC / "crd" / "spec.py", SEAL_SPEC)
    print("pristine rebuilt from app_src, %d files" % len(walk(DST)))
    return 0


if __name__ == "__main__":
    sys.exit(check() if "--check" in sys.argv else copy())
