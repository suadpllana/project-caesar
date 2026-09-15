"""Time one set of kv modules over the graded population, the way the verifier runs it.

    python time_set.py <modules-dir> [--per N] [--seed S] [--fam a,b] [--only-big]

Prints per-family totals and the whole-set total, unbuffered, so a long run is legible
while it happens (CLAUDE.md: stdout buffering looks exactly like a hang).
"""
import argparse
import pathlib
import shutil
import sys
import tempfile
import time

HERE = pathlib.Path(__file__).resolve().parent
TASK = HERE.parent.parent / "tasks" / "page-window-reuse"
SRC = TASK / "environment" / "app_src"
PARTS = ("pool.py", "keep.py", "live.py", "fill.py", "turn.py", "put.py")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mods")
    ap.add_argument("--per", type=int, default=39)
    ap.add_argument("--seed", default="clock")
    ap.add_argument("--fam", default="")
    ap.add_argument("--only-big", action="store_true")
    ap.add_argument("--cap", type=float, default=0)
    args = ap.parse_args()

    sys.path.insert(0, str(TASK / "tests"))
    import gen

    room = pathlib.Path(tempfile.mkdtemp(prefix="pwr-time-"))
    app = room / "app"
    shutil.copytree(SRC, app)
    for part in PARTS:
        one = pathlib.Path(args.mods) / part
        if one.is_file():
            shutil.copy(one, app / "kv" / part)
    sys.path.insert(0, str(app))
    import ops
    from kv import store

    want = set(args.fam.split(",")) if args.fam else None
    by = {}
    lines = 0
    whole = 0.0
    for fam, name, prog in gen.programs(args.seed, args.per):
        if want and fam not in want:
            continue
        if args.only_big and fam not in ("wide", "deep"):
            continue
        t0 = time.time()
        kv = store.Kv()
        for line in prog:
            ops.ex(kv, tuple(line.split()))
        took = time.time() - t0
        whole += took
        lines += len(kv.out)
        by[fam] = by.get(fam, 0.0) + took
        if fam in ("wide", "deep"):
            print("   %-8s %7.2fs  %6d lines" % (name, took, len(kv.out)), flush=True)
        if args.cap and whole > args.cap:
            print("OVER %.0fs after %s" % (args.cap, name), flush=True)
            return 1
    for fam in sorted(by):
        print("%-8s %7.2fs" % (fam, by[fam]), flush=True)
    print("total    %7.2fs over %d lines" % (whole, lines), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
