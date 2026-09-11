"""Differential check: the reference against the sealed model over a whole population.

Both are run in this process, so a run over several hundred plans costs seconds rather than
several hundred interpreter starts. Any disagreement is printed with the first differing line
and the plan that produced it, and the exit status is 1.

Usage: agree.py [seed] [per] [--scale N] [--only FAMILY]
"""
import argparse
import importlib
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
TASK = ROOT / "tasks" / "layer-graft-ask"
sys.path.insert(0, str(TASK / "tests"))
sys.path.insert(0, str(TASK / "tests" / "seal"))
sys.path.insert(0, str(HERE))

import gen  # noqa: E402
import lab  # noqa: E402
import model  # noqa: E402


def load_reference(extra=()):
    work = lab.stage([TASK / "solution"] + list(extra))
    sys.path.insert(0, str(work))
    for name in ("cfg", "cfg.lex", "cfg.say", "cfg.pile", "cfg.made", "cfg.past",
                 "cfg.roll", "cfg.work", "cfg.ans"):
        sys.modules.pop(name, None)
    lex = importlib.import_module("cfg.lex")
    past = importlib.import_module("cfg.past")
    ans = importlib.import_module("cfg.ans")

    def run(text):
        plan = lex.parse(text)
        hist = past.build(plan)
        return [ans.answer(hist, q) for q in plan.asks]

    return run, work


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("seed", nargs="?", default="agree")
    ap.add_argument("per", nargs="?", type=int, default=40)
    ap.add_argument("--scale", type=int, default=1)
    ap.add_argument("--only", default=None)
    args = ap.parse_args(argv[1:])

    run, work = load_reference()
    progs = gen.programs(args.seed, args.per, scale=args.scale)
    if args.only:
        progs = [(n, t) for n, t in progs if n.startswith(args.only)]
    bad = 0
    for name, text in progs:
        got = run(text)
        want = model.trace(text)
        if got != want:
            bad += 1
            for i, (g, w) in enumerate(zip(got, want)):
                if g != w:
                    print("%s line %d: reference %r  model %r" % (name, i, g, w), flush=True)
                    break
            else:
                print("%s: %d lines against %d" % (name, len(got), len(want)), flush=True)
            if bad >= 5:
                break
    shutil.rmtree(work, ignore_errors=True)
    print("%d programs, %d disagreements" % (len(progs), bad), flush=True)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
