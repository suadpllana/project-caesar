"""tests/pristine/ is the verifier's own copy of the shipped tree. Copies go stale."""
import filecmp, pathlib, shutil, sys
R = pathlib.Path(__file__).resolve().parents[2] / "tasks/aside-fit-sweep"
SRC = R / "environment/app_src"
DST = R / "tests/pristine"


def walk(base):
    return sorted(str(p.relative_to(base)) for p in base.rglob("*")
                  if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc")


def main():
    check = "--check" in sys.argv
    if check:
        if not DST.is_dir():
            sys.exit("pristine missing")
        a, b = walk(SRC), walk(DST)
        if a != b:
            sys.exit("pristine differs in file list: %s" % (set(a) ^ set(b)))
        bad = [n for n in a if not filecmp.cmp(SRC / n, DST / n, shallow=False)]
        if bad:
            sys.exit("pristine is stale: %s" % bad)
        print("pristine matches (%d files)" % len(a))
        return
    if DST.exists():
        shutil.rmtree(DST)
    shutil.copytree(SRC, DST, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    print("synced %d files" % len(walk(DST)))


main()
