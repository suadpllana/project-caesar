"""Does the reference, run through the shipped runtime, agree with the sealed model?

The two were written independently - frames and heaps on one side, trails and bucketed
trip prices on the other - so they agree only where they agree about the rules. This runs
both over the hand cases and over a generated population far larger than a verifier run,
in both paces, and prints the first row that differs for every session that does.

    python authoring/repair-orderbook-engine/agree.py [small] [fill] [deep]
    python authoring/repair-orderbook-engine/agree.py --dir <solution-dir> [...]
"""
import argparse
import os
import pathlib
import secrets
import shutil
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
TASK = ROOT / "tasks" / "repair-orderbook-engine"
TESTS = TASK / "tests"
sys.path.insert(0, str(TESTS))

import cases  # noqa: E402
import gen  # noqa: E402
import oracle  # noqa: E402


def tree_with(solution):
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="agree-"))
    app = tmp / "app"
    shutil.copytree(TASK / "environment" / "app_src", app,
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    for f in ("take.py", "shown.py", "hand.py", "hold.py", "trip.py"):
        src = pathlib.Path(solution) / f
        if src.is_file():
            shutil.copy(src, app / "eng" / f)
    return tmp, app


def runtime(app):
    for n in list(sys.modules):
        if n in ("mkt", "eng") or n.startswith("mkt.") or n.startswith("eng."):
            del sys.modules[n]
    sys.path.insert(0, str(app))
    from mkt.drv import drive
    from mkt.rd import read
    sys.path.pop(0)

    def run(text):
        rows = []
        cap, mark, msgs = read(text)
        drive(cap, mark, msgs, rows.append)
        return [list(r) for r in rows]
    return run


def show(row):
    return " ".join(str(c) for c in row) if row else "nothing"


def first_diff(mine, want):
    for i in range(max(len(mine), len(want))):
        a = mine[i] if i < len(mine) else None
        b = want[i] if i < len(want) else None
        if a != b:
            return "event %d: got %s, expected %s" % (i, show(a), show(b))
    return None


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=str(TASK / "solution"))
    ap.add_argument("--small", type=int, default=1200)
    ap.add_argument("--fill", type=int, default=600)
    ap.add_argument("--deep", type=int, default=2)
    ap.add_argument("--filldeep", type=int, default=1)
    ap.add_argument("--nonce", default=None)
    args = ap.parse_args(argv[1:])
    nonce = args.nonce or secrets.token_hex(8)

    plan = [(n, cases.SESS[n]) for n in sorted(cases.SESS)]
    plan += gen.batch(nonce, args.small)
    plan += gen.fill_batch(nonce, args.fill)
    plan += gen.deep_batch(nonce, args.deep)
    plan += gen.fill_deep_batch(nonce, args.filldeep)

    tmp, app = tree_with(args.dir)
    try:
        run = runtime(app)
        bad = 0
        raised = 0
        for name, text in plan:
            want = [list(r) for r in oracle.solve(text)]
            try:
                mine = run(text)
            except Exception as exc:  # noqa: BLE001 - report and carry on
                raised += 1
                print("RAISED %s: %r" % (name, exc))
                continue
            d = first_diff(mine, want)
            if d:
                bad += 1
                if bad <= 12:
                    print("DIFF %s: %s" % (name, d))
        print("nonce %s: %d sessions, %d differ, %d raised" % (nonce, len(plan), bad, raised))
        return 1 if (bad or raised) else 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
