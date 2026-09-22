#!/usr/bin/env python3
"""Keep tests/pristine in step with the shipped tree, and say when it is not.

The verifier lays the six submitted files over its own copy of everything else, so that
copy has to be the tree the agent was given. A stale copy makes the oracle fail inside the
worker with an import error, which reads like a broken task rather than a stale mirror.

The sample list files are deliberately left out: the worker generates and enumerates its
own programs and never reads them, and they are megabytes.

    python3 -u authoring/page-pass-owe/sync.py            copy
    python3 -u authoring/page-pass-owe/sync.py --check    report drift, exit 1 on any
"""
import filecmp
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
TASK = ROOT / "tasks" / "page-pass-owe"
SRC = TASK / "environment" / "app_src"
DST = TASK / "tests" / "pristine"

WANT = ["run_lst.py", "lst/__init__.py", "lst/spec.py", "lst/say.py",
        "lst/seq.py", "lst/scr.py", "lst/owe.py", "lst/pg.py", "lst/edt.py", "lst/rep.py"]


def main(argv):
    check = "--check" in argv
    bad = []
    for rel in WANT:
        a, b = SRC / rel, DST / rel
        if not a.is_file():
            bad.append("missing in environment: %s" % rel)
            continue
        if not b.is_file():
            bad.append("missing in pristine: %s" % rel)
        elif not filecmp.cmp(a, b, shallow=False):
            bad.append("differs: %s" % rel)
        if not check:
            b.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(a, b)
    extra = []
    if DST.is_dir():
        for p in sorted(DST.rglob("*")):
            if p.is_file() and str(p.relative_to(DST)).replace("\\", "/") not in WANT:
                extra.append("not in the shipped tree: %s" % p.relative_to(DST))
    for line in bad + extra:
        print(line, flush=True)
    if check:
        if bad or extra:
            print("pristine is stale", flush=True)
            return 1
        print("pristine matches the shipped tree", flush=True)
        return 0
    for line in extra:
        (DST / line.split(": ", 1)[1]).unlink()
    print("synced %d files" % len(WANT), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
