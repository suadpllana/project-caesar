#!/usr/bin/env python3
"""Differential: a module set against the sealed model, over the generated population.

    python3 -u authoring/page-pass-owe/diff.py solution
    python3 -u authoring/page-pass-owe/diff.py --seed x --per 60 solution

Prints, per family, how many programs the module set and the model disagree on. The
reference must disagree on nothing; a wrong reading is measured by how much it moves.
"""
import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
TASK = ROOT / "tasks" / "page-pass-owe"
PARTS = ("seq", "scr", "owe", "pg", "edt", "rep")

DRIVER = r'''
import json, sys
sys.path.insert(0, %(tree)r)
sys.path.insert(0, %(tests)r)
sys.path.insert(0, %(seal)r)
import gen, model, run_lst
work = gen.programs(%(seed)r, %(per)d)
if %(fam)r:
    work = [w for w in work if w[0] == %(fam)r]
bad = {}
seen = {}
first = {}
for fam, name, lines in work:
    text = "\n".join(lines) + "\n"
    seen[fam] = seen.get(fam, 0) + 1
    want = model.run(text)
    try:
        got = run_lst.run(text)
    except Exception as exc:
        got = ["!! %%s" %% exc]
    if got != want:
        bad[fam] = bad.get(fam, 0) + 1
        if fam not in first:
            first[fam] = name
sys.stdout.write(json.dumps([seen, bad, first]))
'''


def build(src: Path) -> Path:
    tmp = Path(tempfile.mkdtemp(prefix="ppo-d-"))
    shutil.copytree(TASK / "environment" / "app_src", tmp / "app")
    for part in PARTS:
        shutil.copyfile(src / (part + ".py"), tmp / "app" / "lst" / (part + ".py"))
    return tmp


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("modules")
    ap.add_argument("--fam", default="")
    ap.add_argument("--per", type=int, default=40)
    ap.add_argument("--seed", default="diff")
    args = ap.parse_args()

    src = Path(args.modules)
    if not src.is_absolute():
        src = ROOT / args.modules if (ROOT / args.modules).is_dir() else TASK / args.modules
    tree = build(src)
    code = DRIVER % {"tree": str(tree / "app"), "tests": str(TASK / "tests"),
                     "seal": str(TASK / "tests" / "seal"), "seed": args.seed,
                     "per": args.per, "fam": args.fam}
    done = subprocess.run([sys.executable, "-u", "-c", code], capture_output=True, text=True)
    shutil.rmtree(tree, ignore_errors=True)
    if done.returncode != 0:
        sys.stderr.write(done.stderr)
        return done.returncode
    seen, bad, first = json.loads(done.stdout)
    total_bad = 0
    total_seen = 0
    for fam in sorted(seen):
        n, b = seen[fam], bad.get(fam, 0)
        total_seen += n
        total_bad += b
        print("%-8s %4d/%-4d  %5.1f%%  %s"
              % (fam, b, n, 100.0 * b / n, first.get(fam, "")), flush=True)
    print("ALL      %4d/%-4d  %5.1f%%" % (total_bad, total_seen,
                                          100.0 * total_bad / max(total_seen, 1)), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
