"""Keep tests/pristine/ an exact copy of environment/app_src/.

The worker lays the five submitted files over tests/pristine/, so a stale copy grades a tree
the agent never had - which once read as a broken task rather than a stale mirror (CLAUDE.md,
publish-settle-order). Run after any change to environment/; --check only reports.

    python3 authoring/journal-gap-mend/sync_pristine.py [--check]
"""
import filecmp
import pathlib
import shutil
import sys

TASK = pathlib.Path(__file__).resolve().parents[2] / "tasks" / "journal-gap-mend"
SRC = TASK / "environment" / "app_src"
DST = TASK / "tests" / "pristine"


def files(root):
    return sorted(p.relative_to(root) for p in root.rglob("*")
                  if p.is_file() and "__pycache__" not in p.parts)


def main(argv):
    check = "--check" in argv
    want, have = files(SRC), files(DST) if DST.is_dir() else []
    stale = [str(p) for p in want if p not in have or not filecmp.cmp(SRC / p, DST / p, shallow=False)]
    extra = [str(p) for p in have if p not in want]
    if check:
        if stale or extra:
            print("pristine is stale: differs %s, extra %s" % (stale, extra))
            return 1
        print("pristine matches environment/app_src (%d files)" % len(want))
        return 0
    if DST.exists():
        shutil.rmtree(DST)
    shutil.copytree(SRC, DST, ignore=shutil.ignore_patterns("__pycache__"))
    print("pristine rewritten from environment/app_src (%d files)" % len(want))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
