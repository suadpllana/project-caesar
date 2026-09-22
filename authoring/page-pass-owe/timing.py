#!/usr/bin/env python3
"""Time a module set over the graded set, or over one family.

    python3 -u authoring/page-pass-owe/timing.py solution
    python3 -u authoring/page-pass-owe/timing.py environment/app_src/lst --fam wide

Every tree is assembled in a temp dir outside the bundle. Output is flushed as it goes:
a timing harness whose output sits in a buffer looks exactly like a hang.
"""
import argparse
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
TASK = ROOT / "tasks" / "page-pass-owe"
PARTS = ("seq", "scr", "owe", "pg", "edt", "rep")

DRIVER = r'''
import json, sys, time
sys.path.insert(0, %(tree)r)
sys.path.insert(0, %(tests)r)
import gen, run_lst
work = gen.programs(%(seed)r, %(per)d)
if %(fam)r:
    work = [w for w in work if w[0] == %(fam)r]
out = []
for fam, name, lines in work:
    t0 = time.perf_counter()
    got = run_lst.run("\n".join(lines) + "\n")
    out.append([fam, name, time.perf_counter() - t0, len(got)])
sys.stdout.write(json.dumps(out))
'''


def build(src: Path) -> Path:
    tmp = Path(tempfile.mkdtemp(prefix="ppo-t-"))
    shutil.copytree(TASK / "environment" / "app_src", tmp / "app")
    for part in PARTS:
        shutil.copyfile(src / (part + ".py"), tmp / "app" / "lst" / (part + ".py"))
    return tmp


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("modules")
    ap.add_argument("--fam", default="")
    ap.add_argument("--per", type=int, default=40)
    ap.add_argument("--seed", default="timing")
    ap.add_argument("--limit", type=float, default=0.0)
    args = ap.parse_args()

    src = Path(args.modules)
    if not src.is_absolute():
        src = ROOT / args.modules if (ROOT / args.modules).is_dir() else TASK / args.modules
    tree = build(src)
    code = DRIVER % {"tree": str(tree / "app"), "tests": str(TASK / "tests"),
                     "seed": args.seed, "per": args.per, "fam": args.fam}
    t0 = time.perf_counter()
    done = subprocess.run([sys.executable, "-u", "-c", code], capture_output=True, text=True,
                          timeout=args.limit or None)
    wall = time.perf_counter() - t0
    shutil.rmtree(tree, ignore_errors=True)
    if done.returncode != 0:
        sys.stderr.write(done.stderr)
        return done.returncode
    import json
    rows = json.loads(done.stdout)
    by_fam = {}
    for fam, name, sec, nlines in rows:
        got = by_fam.setdefault(fam, [0.0, 0, 0.0])
        got[0] += sec
        got[1] += 1
        got[2] = max(got[2], sec)
    print("%-8s %6s %10s %10s" % ("family", "progs", "total s", "worst s"), flush=True)
    for fam in sorted(by_fam):
        tot, n, worst = by_fam[fam]
        print("%-8s %6d %10.3f %10.3f" % (fam, n, tot, worst), flush=True)
    print("%-8s %6d %10.3f  (wall %.1f s incl. generation)"
          % ("ALL", len(rows), sum(r[2] for r in rows), wall), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
