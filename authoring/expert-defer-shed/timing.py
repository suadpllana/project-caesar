#!/usr/bin/env python3
"""Time the reference and the exactly-correct scanning implementations. Never ships.

The gate is only real if it is measured: two of three scaling boundaries on an earlier task
did not bite when the numbers were finally run. Output is flushed, because a timing harness
that buffers looks exactly like a hang.

    python3 -u authoring/expert-defer-shed/timing.py [--fams wide,deep] [--which ...]
"""
import argparse
import resource
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import emit  # noqa: E402
import lab  # noqa: E402

SLOW = {
    "slow-weakest": emit.slow_weakest,
    "slow-free": emit.slow_free,
    "slow-shed": emit.slow_shed,
}

RUNNER = """
import resource, sys, time
sys.path.insert(0, %r)
resource.setrlimit(resource.RLIMIT_AS, (%d, %d))
import run_lay
text = open(%r, encoding="utf-8").read()
t0 = time.time()
lines = run_lay.run(text)
print("SECONDS %%.3f LINES %%d" %% (time.time() - t0, len(lines)))
"""


def timed(here, prog, cap_mb, limit):
    """One program under a memory cap, in its own process, with a wall clock."""
    script = RUNNER % (str(here), cap_mb * 1024 * 1024, cap_mb * 1024 * 1024, str(prog))
    room = Path(tempfile.mkdtemp(prefix="eds-time-"))
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
    ap.add_argument("--limit", type=int, default=400)
    ap.add_argument("--seed", default="timing")
    args = ap.parse_args()

    _cases, gen, _model = lab.sealed()
    import random

    ref = lab.tree(lab.SOL)
    trees = {"reference": ref}
    for name, build in SLOW.items():
        build()
        trees[name] = lab.tree(files=emit.BUILT[name])

    room = Path(tempfile.mkdtemp(prefix="eds-progs-"))
    for fam in args.fams.split(","):
        for i in range(args.per):
            rng = random.Random("%s|%s|%d" % (args.seed, fam, i))
            lines = gen.build(fam, rng)
            prog = room / ("%s-%d.txt" % (fam, i))
            prog.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
            tokens = sum(1 for ln in lines if ln.startswith("t "))
            print("%s-%d  %d tokens, %d lines" % (fam, i, tokens, len(lines)), flush=True)
            for label, here in trees.items():
                secs, note = timed(here, prog, args.mem, args.limit)
                print("    %-14s %s" % (label, note if secs is None else "%.3fs" % secs),
                      flush=True)
    print("peak rss of this process: %d MB"
          % (resource.getrusage(resource.RUSAGE_SELF).ru_maxrss // 1024))
    return 0


if __name__ == "__main__":
    sys.exit(main())
