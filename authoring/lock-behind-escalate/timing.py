#!/usr/bin/env python3
"""Time the sealed model, the reference and any policy directory on the scale families.

Each run is its own process under a memory cap and a wall clock, with the output flushed as
it comes, because a timing harness that buffers looks exactly like a hang (CLAUDE.md).

    python3 -u authoring/lock-behind-escalate/timing.py [--fams wide,deep] [--per 1]
                                                          [--which model,reference,DIR ...]
"""
import argparse
import random
import resource
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lab  # noqa: E402

RUNNER_TREE = """
import resource, sys, time
sys.path.insert(0, %r)
resource.setrlimit(resource.RLIMIT_AS, (%d, %d))
import run_lm
text = open(%r, encoding="utf-8").read()
t0 = time.time()
lines = run_lm.run(text)
print("SECONDS %%.3f LINES %%d" %% (time.time() - t0, len(lines)))
"""

RUNNER_MODEL = """
import resource, sys, time
sys.path.insert(0, %r)
resource.setrlimit(resource.RLIMIT_AS, (%d, %d))
import model
lines = open(%r, encoding="utf-8").read().splitlines()
t0 = time.time()
out = model.expect(lines)
print("SECONDS %%.3f LINES %%d" %% (time.time() - t0, len(out)))
"""


def timed(script, cap_mb, limit):
    room = Path(tempfile.mkdtemp(prefix="lbe-time-"))
    runner = room / "go.py"
    runner.write_text(script, encoding="utf-8", newline="\n")
    t0 = time.time()
    try:
        done = subprocess.run([sys.executable, "-u", str(runner)], capture_output=True,
                              text=True, timeout=limit)
    except subprocess.TimeoutExpired:
        return None, "over %ds" % limit
    spent = time.time() - t0
    if done.returncode != 0:
        tail = done.stderr.strip().splitlines()[-1:] or ["exit %d" % done.returncode]
        return None, "%s after %.1fs" % (tail[0][:70], spent)
    return float(done.stdout.split()[1]), done.stdout.strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fams", default="wide,deep")
    ap.add_argument("--per", type=int, default=1)
    ap.add_argument("--mem", type=int, default=2048)
    ap.add_argument("--limit", type=int, default=600)
    ap.add_argument("--seed", default="timing")
    ap.add_argument("--which", default="model,reference")
    args = ap.parse_args()

    _cases, gen, _model = lab.sealed()
    cap = args.mem * 1024 * 1024
    trees = {}
    for which in args.which.split(","):
        if which == "model":
            trees[which] = None
        elif which == "reference":
            trees[which] = lab.tree(lab.SOL)
        else:
            trees[Path(which).name] = lab.tree(which)

    room = Path(tempfile.mkdtemp(prefix="lbe-progs-"))
    for fam in args.fams.split(","):
        for i in range(args.per):
            rng = random.Random("%s|%s|%d" % (args.seed, fam, i))
            lines = gen.build(fam, rng)
            prog = room / ("%s-%d.txt" % (fam, i))
            prog.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
            ops = sum(1 for ln in lines if not ln.startswith("cfg"))
            print("%s-%d  %d ops" % (fam, i, ops), flush=True)
            for label, here in trees.items():
                if here is None:
                    script = RUNNER_MODEL % (str(lab.TASK / "tests" / "seal"), cap, cap, str(prog))
                else:
                    script = RUNNER_TREE % (str(here), cap, cap, str(prog))
                secs, note = timed(script, args.mem, args.limit)
                print("    %-14s %s" % (label, note if secs is None else "%.3fs" % secs),
                      flush=True)
    print("peak rss of this process: %d MB"
          % (resource.getrusage(resource.RUSAGE_SELF).ru_maxrss // 1024))
    return 0


if __name__ == "__main__":
    sys.exit(main())
