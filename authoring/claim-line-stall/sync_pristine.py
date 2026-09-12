"""Keep tests/pristine in step with environment/app_src.

The worker lays the six submitted files over this copy, so anything else the agent touched
cannot change what a program prints. A copy goes stale: rebuilding the environment without
re-running this makes the oracle fail with an ImportError inside the worker, which reads like
a broken task rather than a stale mirror. `--check` is the gate; run it after any change to
environment/.

`progs/` is left out on purpose: the worker generates its own programs and the shipped ones
are megabytes of text.
"""
import filecmp
import pathlib
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
TASK = ROOT / "tasks" / "claim-line-stall"
SRC = TASK / "environment" / "app_src"
DST = TASK / "tests" / "pristine"
SKIP = {"progs", "__pycache__"}


def wanted():
    out = []
    for path in sorted(SRC.rglob("*")):
        rel = path.relative_to(SRC)
        if any(part in SKIP for part in rel.parts):
            continue
        if path.is_file():
            out.append(rel)
    return out


def main():
    check = "--check" in sys.argv
    want = wanted()
    bad = []
    for rel in want:
        there = DST / rel
        if not there.is_file() or not filecmp.cmp(SRC / rel, there, shallow=False):
            bad.append(rel)
            if not check:
                there.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(SRC / rel, there)
    extra = []
    if DST.is_dir():
        for path in sorted(DST.rglob("*")):
            rel = path.relative_to(DST)
            if path.is_file() and rel not in want:
                extra.append(rel)
                if not check:
                    path.unlink()
    if check:
        if bad or extra:
            print("pristine is stale: %d differ, %d extra" % (len(bad), len(extra)))
            for rel in bad + extra:
                print("   %s" % rel)
            return 1
        print("pristine matches app_src (%d files)" % len(want))
        return 0
    print("synced %d files, %d copied, %d removed" % (len(want), len(bad), len(extra)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
