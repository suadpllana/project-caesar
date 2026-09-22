"""Time the whole graded set the way the worker runs it: one process, every document in turn.

    python3 -u time_all.py <pane> [per] [seed] [--limit S]

<pane> is solution, a directory of six pane files, or `model` for the sealed model. Stops once
the elapsed time passes --limit and says so, so a reading that cannot finish is reported as that.
--each prints a line after every large document, so a run killed from outside still leaves
the documents it finished and how long each took.
"""
import os
import sys
import time

os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
sys.dont_write_bytecode = True
import lab  # noqa: E402

cases, gen, model = lab.sealed()


def main(argv):
    args = [a for i, a in enumerate(argv[1:], 1)
            if not a.startswith("--") and argv[i - 1] != "--limit"]
    which = args[0]
    per = int(args[1]) if len(args) > 1 else 30
    seed = args[2] if len(args) > 2 else "timing"
    limit = float(argv[argv.index("--limit") + 1]) if "--limit" in argv else 1e9
    each = "--each" in argv
    run = model.expect if which == "model" else lab.pane(which)
    work = [("hand", n, cases.prog(n)) for n in cases.ORDER] + gen.programs(seed, per)
    fams = {}
    t0 = time.time()
    for fam, name, lines in work:
        t = time.time()
        run(lines)
        fams[fam] = fams.get(fam, 0.0) + time.time() - t
        if each and fam in ("wide", "deep", "long"):
            print("  %s %.1f s (elapsed %.1f s)" % (name, time.time() - t, time.time() - t0))
        if time.time() - t0 > limit:
            print("%s: passed the %.0f s limit at %s after %.1f s" % (which, limit, name, time.time() - t0))
            return 1
    total = time.time() - t0
    big = " ".join("%s %.1f" % (f, fams[f]) for f in ("wide", "deep", "long"))
    print("%s: %d documents in %.1f s  (%s; rest %.1f)" % (
        which, len(work), total, big, total - sum(fams[f] for f in ("wide", "deep", "long"))))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
