"""Build the two scale families and time the candidate against the naive walk."""
import random
import sys
import time

sys.path.insert(0, ".")
import fast
import naive


def wide(n, ops, seed=5):
    """Import n rows, then roll and pass across them with occasional edits."""
    rng = random.Random(seed)
    out = ["bulk %d 30 170" % n]
    for i in range(ops):
        k = i % 10
        if k in (0, 3, 6):
            out.append("roll %d" % rng.choice([-4000, -900, 700, 1500, 9000, 40000]))
        elif k in (1, 4, 7):
            out.append("pass")
        elif k == 2:
            out.append("top")
        elif k == 5:
            out.append("tall")
        elif k == 8:
            out.append("face")
        else:
            out.append("set k%d %d" % (rng.randrange(1, n + 1), rng.choice([20, 300])))
    out += ["top", "tall", "face"]
    return out


def deep(n, ops, seed=7):
    """Import n rows, measure a stretch of them, then edit at the front."""
    rng = random.Random(seed)
    out = ["bulk %d 40 90" % n]
    for _ in range(30):
        out += ["roll 2000", "pass"]
    for i in range(ops):
        k = i % 8
        if k == 0:
            out.append("ins %d y%d %d" % (rng.randrange(4), i, rng.choice([10, 400])))
        elif k == 1:
            out.append("del y%d" % (i - 1))
        elif k in (2, 5):
            out.append("pass")
        elif k == 3:
            out.append("move k%d %d" % (rng.randrange(1, n + 1), rng.randrange(3)))
        elif k == 4:
            out.append("top")
        elif k == 6:
            out.append("tall")
        else:
            out.append("face")
    out += ["top", "tall", "face"]
    return out


def timed(mod, lines, cap=400.0):
    t = time.time()
    out = mod.run(lines)
    return time.time() - t, out


def main():
    for name, lines in (("wide", wide(int(sys.argv[1]), int(sys.argv[2]))),
                        ("deep", deep(int(sys.argv[3]), int(sys.argv[4])))):
        print("%s: %d lines" % (name, len(lines)), flush=True)
        tf, of = timed(fast, lines)
        print("  fast  %7.2fs  %d events" % (tf, len(of)), flush=True)
        tn, on = timed(naive, lines)
        print("  naive %7.2fs  %d events  %s" % (tn, len(on), "AGREE" if on == of else "DIFFER"),
              flush=True)
        print("  ratio %.0fx" % (tn / tf if tf else 0), flush=True)


if __name__ == "__main__":
    main()
