"""Keep tests/pristine/ the same tree as environment/app_src/.

The verifier lays the submitted files over its own copy, so a stale copy makes the oracle fail
with an import error inside the worker, which reads like a broken task rather than a mirror
nobody re-synced.

    python authoring/stale-cover-serve/sync_pristine.py [--check]
"""
import filecmp
import pathlib
import shutil
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lab  # noqa: E402

MIRROR = lab.TASK / "tests" / "pristine"


SKIP = shutil.ignore_patterns("__pycache__", "*.pyc")


def walk(root):
    return sorted(p.relative_to(root).as_posix() for p in root.rglob("*")
                  if p.is_file() and "__pycache__" not in p.parts)


def main():
    check = "--check" in sys.argv
    if check:
        if not MIRROR.is_dir():
            print("pristine/ is missing")
            return 1
        left, right = walk(lab.SRC), walk(MIRROR)
        if left != right:
            print("file lists differ: only in app_src %s; only in pristine %s"
                  % (sorted(set(left) - set(right)), sorted(set(right) - set(left))))
            return 1
        bad = [rel for rel in left
               if not filecmp.cmp(lab.SRC / rel, MIRROR / rel, shallow=False)]
        if bad:
            print("contents differ: %s" % bad)
            return 1
        print("pristine/ matches app_src/: %d files" % len(left))
        return 0
    shutil.rmtree(MIRROR, ignore_errors=True)
    shutil.copytree(lab.SRC, MIRROR, ignore=SKIP)
    print("synced %d files into %s" % (len(walk(MIRROR)), MIRROR))
    return 0


if __name__ == "__main__":
    sys.exit(main())
