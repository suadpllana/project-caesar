"""Keep tests/pristine in step with the shipped tree.

The verifier lays the submitted files over its own copy of the tree, so that copy has to be
the one the agent was given. A stale copy makes the oracle fail inside the worker with an
import error, which reads like a broken task rather than a stale mirror.

    python sync.py            copy environment/app_src over tests/pristine
    python sync.py --check    report any difference and exit 1
"""
import filecmp
import pathlib
import shutil
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lab  # noqa: E402

DEST = lab.TASK / "tests" / "pristine"


def walk(root):
    return sorted(p.relative_to(root).as_posix() for p in root.rglob("*")
                  if p.is_file() and "__pycache__" not in p.parts)


def main():
    check = "--check" in sys.argv
    src = walk(lab.SRC)
    if not DEST.exists():
        if check:
            print("pristine copy is missing")
            return 1
        shutil.copytree(lab.SRC, DEST)
        print("created %s with %d files" % (DEST, len(src)))
        return 0
    have = walk(DEST)
    bad = [n for n in set(src) | set(have)
           if n not in src or n not in have
           or not filecmp.cmp(lab.SRC / n, DEST / n, shallow=False)]
    if check:
        if bad:
            print("pristine copy differs on: %s" % ", ".join(sorted(bad)))
            return 1
        print("pristine copy matches the shipped tree (%d files)" % len(src))
        return 0
    shutil.rmtree(DEST)
    shutil.copytree(lab.SRC, DEST)
    print("synced %d files into %s%s" % (len(src), DEST,
                                         "" if not bad else " (was stale on %d)" % len(bad)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
