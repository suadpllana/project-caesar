"""Per-program margin on the graded wide families: the reference against the row-list walk.

The whole-set figure is what the limit is applied to, but the ratio it hides is worth
knowing per program, because the naive cost depends on where the view is sitting - a prefix
read by walking the list costs the index of the row it is asked about.
"""
import sys
import time

sys.path.insert(0, ".")
sys.path.insert(0, "/home/user/project-caesar/tasks/anchor-mean-settle/tests")
import gen  # noqa: E402
import probe  # noqa: E402

REF = "/home/user/project-caesar/tasks/anchor-mean-settle/solution"


def main():
    for seed in sys.argv[1:] or ["final-timing"]:
        for fam, name, lines in gen.programs(seed, 1):
            if fam not in ("wide", "deep"):
                continue
            t = time.time()
            probe.run(REF, [(name, lines)], limit=300)
            r = time.time() - t
            t = time.time()
            got, err = probe.run("slow/walk", [(name, lines)], limit=1500)
            w = time.time() - t
            print("%-14s %-8s ref %6.2fs  walk %8.2fs  %5.0fx  err=%s"
                  % (seed, name, r, w, w / r if r else 0, err), flush=True)


if __name__ == "__main__":
    main()
