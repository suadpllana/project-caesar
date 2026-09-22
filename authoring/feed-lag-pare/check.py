"""Three-way differential test for feed-lag-pare.

  slow.py      a direct transcription of the contract, written for obviousness
  solution/    the reference, carrying a pair heap across commands
  tests/seal/  the sealed model, composing each stretch into one effect

All three must agree. The random programs go through all three; the generated population is
too large for the transcription, so there the reference and the model check each other.

Usage:
    python authoring/feed-lag-pare/check.py random [count]
    python authoring/feed-lag-pare/check.py population [per]
    python authoring/feed-lag-pare/check.py cases
"""
import sys as _sys

# Importing the bundle's own modules must not leave a __pycache__ inside
# tasks/<slug>/: authoring scratch that lands in the task folder has been packaged
# before (CLAUDE.md, token-seam-emit).
_sys.dont_write_bytecode = True

import os
import random
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
TASK = os.path.join(ROOT, "tasks", "feed-lag-pare")

sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(TASK, "tests"))
sys.path.insert(0, os.path.join(TASK, "tests", "seal"))

import cases  # noqa: E402
import gen  # noqa: E402
import model  # noqa: E402
import slow  # noqa: E402


def reference():
    """Assemble the shipped tree with solution/ laid over it, outside the bundle."""
    room = tempfile.mkdtemp(prefix="flp-ref-")
    tree = os.path.join(room, "app")
    shutil.copytree(os.path.join(TASK, "environment", "app_src"), tree)
    for name in os.listdir(os.path.join(TASK, "solution")):
        if name.endswith(".py"):
            shutil.copy(os.path.join(TASK, "solution", name), os.path.join(tree, "lg", name))
    sys.path.insert(0, tree)
    import run_log
    return run_log, room


def sample(rng):
    keys = rng.choice([2, 3, 5, 8])
    steps = rng.choice([14, 28, 50])
    out = []
    marks, feeds, spare = [], [], ["n%d" % i for i in range(20)]
    head = 0
    for _ in range(steps):
        pick = rng.random()
        if pick < 0.42:
            key = rng.randrange(keys)
            kind = rng.choice(["set", "add", "add", "del"])
            out.append("del %d" % key if kind == "del"
                       else "%s %d %d" % (kind, key, rng.randint(-5, 9)))
            head += 1
        elif pick < 0.53 and spare:
            name = spare.pop()
            out.append("mark %s" % name)
            marks.append(name)
        elif pick < 0.60 and marks:
            out.append("unmark %s" % marks.pop(rng.randrange(len(marks))))
        elif pick < 0.70 and spare:
            name = spare.pop()
            lo = rng.randrange(keys)
            hi = rng.randrange(lo, keys)
            out.append("feed %s %d %d" % (name, lo, hi))
            feeds.append((name, lo, hi))
        elif pick < 0.79 and feeds:
            name = feeds[rng.randrange(len(feeds))][0]
            out.append("ack %s %d" % (name, rng.randint(0, head + 2)))
        elif pick < 0.84 and feeds:
            out.append("close %s" % feeds.pop(rng.randrange(len(feeds)))[0])
        elif pick < 0.91 and (marks or feeds):
            if marks and (not feeds or rng.random() < 0.5):
                out.append("read %s %d" % (rng.choice(marks), rng.randrange(keys)))
            else:
                name, lo, hi = feeds[rng.randrange(len(feeds))]
                out.append("read %s %d" % (name, rng.randint(lo, hi)))
        else:
            out.append("pare %d" % rng.randint(0, 12))
    out.append("pare %d" % rng.randint(0, 6))
    return out


def report(bad, total, what):
    print("%s: %d of %d disagree" % (what, len(bad), total))
    for name, want, got, prog in bad[:2]:
        print("  --- %s\n%s\n  want %s\n  got  %s" % (name, "\n".join(prog), want, got))
    return 1 if bad else 0


def main():
    what = sys.argv[1] if len(sys.argv) > 1 else "random"
    run_log, room = reference()
    try:
        if what == "cases":
            bad = []
            for name in cases.ORDER:
                lines = cases.prog(name)
                want = slow.run("\n".join(lines) + "\n")
                for who, got in (("ref", run_log.run("\n".join(lines) + "\n")),
                                 ("model", model.expect(lines))):
                    if got != want:
                        bad.append(("%s/%s" % (name, who), want, got, lines))
            return report(bad, len(cases.ORDER), "hand cases")
        if what == "random":
            count = int(sys.argv[2]) if len(sys.argv) > 2 else 2000
            bad = []
            for seed in range(count):
                lines = sample(random.Random(seed))
                want = slow.run("\n".join(lines) + "\n")
                for who, got in (("ref", run_log.run("\n".join(lines) + "\n")),
                                 ("model", model.expect(lines))):
                    if got != want:
                        bad.append(("seed %d/%s" % (seed, who), want, got, lines))
            return report(bad, count, "random programs")
        if what == "population":
            per = int(sys.argv[2]) if len(sys.argv) > 2 else 40
            progs = gen.programs("check", per)
            bad = []
            for fam, name, lines in progs:
                want = model.expect(lines)
                got = run_log.run("\n".join(lines) + "\n")
                if got != want:
                    bad.append((name, want[:4], got[:4], lines[:6]))
                    print("  MISMATCH", fam, name, flush=True)
            return report(bad, len(progs), "generated population")
        print(__doc__)
        return 2
    finally:
        shutil.rmtree(room, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
