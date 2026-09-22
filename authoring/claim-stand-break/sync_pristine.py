"""Keep tests/pristine in step with the shipped tree.

The verifier lays the six submitted files over its own copy of the tree, so that copy has to be
the tree the agent was given. A stale copy makes the oracle fail inside the worker, which reads
like a broken task rather than a copy nobody re-synced.
"""
import filecmp
import pathlib
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
SRC = ROOT / "tasks" / "claim-stand-break" / "environment" / "app_src"
DST = ROOT / "tasks" / "claim-stand-break" / "tests" / "pristine"
SKIP = {"progs"}


def wanted():
    for one in SRC.rglob("*"):
        if one.is_file() and one.parts[len(SRC.parts)] not in SKIP:
            yield one.relative_to(SRC)


def main(argv):
    check = "--check" in argv
    bad = []
    seen = set()
    for rel in wanted():
        seen.add(rel)
        dst = DST / rel
        if not dst.is_file() or not filecmp.cmp(SRC / rel, dst, shallow=False):
            bad.append(rel)
            if not check:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(SRC / rel, dst)
    for one in list(DST.rglob("*")):
        if one.is_file() and one.relative_to(DST) not in seen:
            bad.append(one.relative_to(DST))
            if not check:
                one.unlink()
    print("%s: %d file(s) %s" % (DST, len(bad), "out of step" if check else "synced"))
    for rel in bad:
        print("   ", rel)
    return 1 if (check and bad) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
