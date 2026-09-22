"""Keep tests/pristine in step with environment/app_src.

The verifier lays the six submitted files over its own copy of the tree, so that copy has to be
the tree that shipped. A copy goes stale the moment the environment changes, and a stale one
fails the oracle inside the worker with an import error, which reads like a broken task rather
than an out-of-date mirror. Run with --check after any change under environment/.
"""
import filecmp
import shutil
import sys
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lab  # noqa: E402

DEST = lab.TASK / "tests" / "pristine"


def walk(root):
    return sorted(str(p.relative_to(root)) for p in root.rglob("*")
                  if p.is_file() and "__pycache__" not in p.parts)


def main():
    check = "--check" in sys.argv
    want = walk(lab.SRC)
    if check:
        if not DEST.is_dir():
            print("pristine is missing")
            return 1
        have = walk(DEST)
        bad = [p for p in want if p not in have]
        extra = [p for p in have if p not in want]
        diff = [p for p in want if p in have
                and not filecmp.cmp(lab.SRC / p, DEST / p, shallow=False)]
        for name, rows in (("missing", bad), ("extra", extra), ("differs", diff)):
            for row in rows:
                print("%s: %s" % (name, row))
        if bad or extra or diff:
            return 1
        print("pristine matches environment/app_src (%d files)" % len(want))
        return 0
    if DEST.is_dir():
        shutil.rmtree(DEST)
    shutil.copytree(lab.SRC, DEST, ignore=shutil.ignore_patterns("__pycache__"))
    print("pristine synced: %d files" % len(walk(DEST)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
