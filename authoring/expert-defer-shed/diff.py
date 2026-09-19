#!/usr/bin/env python3
"""Reference against the sealed model, over the generated population.

Authoring only; never ships. Writes its scratch tree to a temporary directory outside the
bundle, because a stray .trial/ inside the task folder has been packaged before.

    python3 -u authoring/expert-defer-shed/diff.py [--per N] [--fams a,b] [--time]
"""
import argparse
import importlib
import shutil
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
TASK = ROOT / "tasks" / "expert-defer-shed"
PARTS = ("gate", "cap", "buf", "back", "put", "trim", "tally")


def tree(which):
    room = Path(tempfile.mkdtemp(prefix="eds-"))
    here = room / "app"
    shutil.copytree(TASK / "environment" / "app_src", here)
    if which != "ship":
        for part in PARTS:
            shutil.copy(Path(which) / ("%s.py" % part), here / "lay" / ("%s.py" % part))
    return here


def load(here):
    sys.path.insert(0, str(here))
    for name in list(sys.modules):
        if name == "run_lay" or name == "lay" or name.startswith("lay."):
            del sys.modules[name]
    return importlib.import_module("run_lay")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--per", type=int, default=30)
    ap.add_argument("--fams", default="")
    ap.add_argument("--seed", default="diff")
    ap.add_argument("--time", action="store_true")
    ap.add_argument("--which", default=str(TASK / "solution"))
    args = ap.parse_args()

    sys.path.insert(0, str(TASK / "tests"))
    sys.path.insert(0, str(TASK / "tests" / "seal"))
    import gen
    import model

    here = tree(args.which)
    run_lay = load(here)

    want = set(args.fams.split(",")) if args.fams else None
    work = [p for p in gen.programs(args.seed, args.per) if not want or p[0] in want]

    bad = 0
    spent = {}
    for fam, name, lines in work:
        text = "\n".join(lines) + "\n"
        t0 = time.time()
        got = run_lay.run(text)
        t1 = time.time()
        exp = model.expect(lines)
        t2 = time.time()
        spent.setdefault(fam, [0.0, 0.0, 0])
        spent[fam][0] += t1 - t0
        spent[fam][1] += t2 - t1
        spent[fam][2] += 1
        if got != exp:
            bad += 1
            if bad <= 3:
                print("MISMATCH %s" % name)
                for i, (a, b) in enumerate(zip(got, exp)):
                    if a != b:
                        print("  line %d: got %r want %r" % (i, a, b))
                        break
                if len(got) != len(exp):
                    print("  lengths %d vs %d" % (len(got), len(exp)))
    print("%d programs, %d mismatches" % (len(work), bad))
    if args.time:
        for fam in sorted(spent):
            ref, mod, n = spent[fam]
            print("  %-8s n=%-4d ref %7.3fs  model %7.3fs" % (fam, n, ref, mod))
    shutil.rmtree(here.parent, ignore_errors=True)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
