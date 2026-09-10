"""Keep tests/pristine in step with environment/app_src.

The verifier lays the five submitted modules over its own copy of the tree. That copy is a
copy, and copies go stale: a rebuild of the environment that misses it makes the oracle
fail inside the worker, which reads like a broken task rather than a stale mirror. Run with
--check after any change to environment/.

The example programs are left out. The worker builds every graded program in code and never
reads `progs/`, so mirroring three megabytes of them into the verifier image would only make
the build and the per-run copy slower.
"""
import filecmp
import pathlib
import shutil
import sys

TASK = pathlib.Path(__file__).resolve().parent.parent.parent / "tasks" / "span-claim-charge"
SRC = TASK / "environment" / "app_src"
DST = TASK / "tests" / "pristine"


SKIP = ("__pycache__", "progs")


def walk(root):
    return sorted(p.relative_to(root) for p in root.rglob("*")
                  if p.is_file() and not any(s in p.parts for s in SKIP))


def main():
    check = "--check" in sys.argv
    if check:
        if not DST.is_dir():
            print("tests/pristine is missing")
            return 1
        a, b = walk(SRC), walk(DST)
        if a != b:
            print("file lists differ: only in environment %s; only in pristine %s"
                  % (sorted(set(a) - set(b)), sorted(set(b) - set(a))))
            return 1
        bad = [str(rel) for rel in a if not filecmp.cmp(SRC / rel, DST / rel, shallow=False)]
        if bad:
            print("content differs: %s" % ", ".join(bad))
            return 1
        print("pristine matches environment/app_src (%d files)" % len(a))
        return 0
    if DST.is_dir():
        shutil.rmtree(DST)
    shutil.copytree(SRC, DST, ignore=shutil.ignore_patterns(*SKIP))
    print("synced %d files into tests/pristine" % len(walk(DST)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
