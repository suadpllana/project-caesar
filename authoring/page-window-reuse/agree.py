"""Differential test: one set of kv modules against the sealed model.

Runs in process against a staged tree, the way the verifier's worker does, so a few hundred
programs cost seconds rather than a subprocess each. Prints the first lines that differ.

    python agree.py <modules-dir|-> [--per N] [--seed S] [--fam a,b] [--big]
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


def stage(mods):
    room = pathlib.Path(tempfile.mkdtemp(prefix="pwr-agree-"))
    app = room / "app"
    shutil.copytree(SRC, app)
    if mods not in (None, "-"):
        for part in PARTS:
            one = pathlib.Path(mods) / part
            if one.is_file():
                shutil.copy(one, app / "kv" / part)
    return app


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mods")
    ap.add_argument("--per", type=int, default=8)
    ap.add_argument("--seed", default="agree")
    ap.add_argument("--fam", default="")
    ap.add_argument("--big", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    sys.path.insert(0, str(TASK / "tests"))
    sys.path.insert(0, str(TASK / "tests" / "seal"))
    import gen
    import model

    app = stage(args.mods)
    sys.path.insert(0, str(app))
    import ops
    from kv import store

    want = set(args.fam.split(",")) if args.fam else None
    bad = 0
    n = 0
    slow = []
    for fam, name, lines in gen.programs(args.seed, args.per):
        if want and fam not in want:
            continue
        if not args.big and fam in ("wide", "deep"):
            continue
        n += 1
        t0 = time.time()
        kv = store.Kv()
        try:
            for line in lines:
                ops.ex(kv, tuple(line.split()))
            got = kv.out
        except Exception as exc:
            got = ["RAISED %s: %s" % (type(exc).__name__, exc)]
        t1 = time.time()
        sure = model.expect(lines)
        slow.append((t1 - t0, time.time() - t1, name))
        if got != sure:
            bad += 1
            if bad <= 4:
                print("== %s differs (%d lines against %d)" % (name, len(got), len(sure)))
                for i in range(max(len(got), len(sure))):
                    g = got[i] if i < len(got) else "<none>"
                    s = sure[i] if i < len(sure) else "<none>"
                    if g != s:
                        print("   line %d: got %r want %r" % (i, g, s))
                        break
    slow.sort(reverse=True)
    if not args.quiet:
        for a, b, name in slow[:3]:
            print("   slowest %s: tree %.2fs model %.2fs" % (name, a, b))
    print("%d programs, %d differ" % (n, bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
