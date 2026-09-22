"""Keep tests/pristine in step with environment/app_src.

The overlay the verifier runs is a copy, and copies go stale: rebuilding the environment
without re-syncing makes the oracle fail with an import error inside the worker, which reads
like a broken task rather than a stale mirror. `--check` reports drift without writing.
"""
import filecmp
import pathlib
import shutil
import sys

TASK = pathlib.Path(__file__).resolve().parent.parent.parent / "tasks" / "scan-chunk-pick"
SRC = TASK / "environment" / "app_src"
DST = TASK / "tests" / "pristine"


def files(root):
    return sorted(p.relative_to(root) for p in root.rglob("*")
                  if p.is_file() and "__pycache__" not in p.parts)


def main():
    check = "--check" in sys.argv
    if check:
        if not DST.is_dir():
            raise SystemExit("pristine missing")
        a, b = files(SRC), files(DST)
        drift = [str(p) for p in set(a) ^ set(b)]
        drift += [str(p) for p in a if p in b and not filecmp.cmp(SRC / p, DST / p, shallow=False)]
        if drift:
            raise SystemExit("pristine is stale: %s" % sorted(set(drift)))
        print("pristine matches app_src (%d files)" % len(a))
        return
    if DST.is_dir():
        shutil.rmtree(DST)
    shutil.copytree(SRC, DST, ignore=shutil.ignore_patterns("__pycache__"))
    print("synced %d files into %s" % (len(files(DST)), DST))


if __name__ == "__main__":
    main()
