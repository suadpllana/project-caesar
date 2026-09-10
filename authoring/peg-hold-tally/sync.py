"""Keep tests/pristine in step with environment/app_src. Authoring tool; never ships.

The sample programs are left out of the copy: the worker generates its own programs and never
reads the shipped ones, so carrying several megabytes of them into the verifier image would only
make the bundle bigger.
"""
import filecmp
import pathlib
import shutil
import sys

HERE = pathlib.Path(__file__).resolve().parent
TASK = HERE.parent.parent / "tasks" / "peg-hold-tally"
SRC = TASK / "environment" / "app_src"
DST = TASK / "tests" / "pristine"


SKIP = ("__pycache__", "progs")


def files(root):
    return sorted(str(p.relative_to(root)) for p in root.rglob("*")
                  if p.is_file() and not set(p.parts) & set(SKIP))


def main():
    check = "--check" in sys.argv
    if not check:
        if DST.exists():
            shutil.rmtree(DST)
        shutil.copytree(SRC, DST, ignore=shutil.ignore_patterns(*SKIP))
        print("synced %d files" % len(files(DST)))
        return 0
    if not DST.exists():
        print("pristine missing")
        return 1
    a, b = files(SRC), files(DST)
    bad = [n for n in set(a) | set(b)
           if n not in a or n not in b or not filecmp.cmp(SRC / n, DST / n, shallow=False)]
    print("pristine is stale: %s" % bad if bad else "pristine matches app_src (%d files)" % len(a))
    return 1 if bad else 0


sys.exit(main())
