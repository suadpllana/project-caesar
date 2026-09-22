"""Search for the two trails that ship in the tree, rather than choosing them.

The brief has to print one correct line verbatim or a format slip fails every trail for a
reason that is not the task. But a worked example is an oracle unless it is measured not to be
(CLAUDE.md, 2026-09-06): the trail the line comes from must leave the load-bearing readings
undecided, so a solver cannot read the answer off it.

So: generate candidates, run each under the reference and under every wrong reading, and keep
the smallest that (a) the shipped engine already gets wrong, so the brief has something true to
say about it, and (b) decides as few readings as possible. Ties break on the shorter trail.
"""
import pathlib
import random
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lab  # noqa: E402
import readings as rd  # noqa: E402

_cases, gen, model = lab.sealed()

HEAVY = (
    "pre-same-obs", "credit-recompute", "rearm-now", "rearm-on-touch",
    "void-named-only", "void-cone-shut", "bars-first", "obs-per-action",
    "err-keeps", "bud-per-step", "close-keeps", "bud-spares-failed",
)


def small(rnd):
    """A short trail: a couple of records, two or three goals, a bar, a handful of steps."""
    keys = list(range(rnd.randrange(2, 5)))
    out = ["cfg %d" % rnd.choice((6, 8, 40, 100))]
    for key in keys:
        if rnd.random() < 0.6:
            out.append("rec %d %d" % (key, rnd.randrange(0, 6)))
    out.append("ep %s" % rnd.choice(("one", "run", "a1", "t0")))
    goals = rnd.randrange(2, 4)
    for gid in range(goals):
        pre = [rnd.randrange(gid)] if gid and rnd.random() < 0.6 else []
        kind = rnd.choice(("at", "up", "off"))
        key = rnd.choice(keys)
        head = "goal %d %d %d" % (gid, rnd.randrange(1, 4), len(pre))
        if pre:
            head += " " + " ".join(str(x) for x in pre)
        out.append("%s off %d" % (head, key) if kind == "off"
                   else "%s %s %d %d" % (head, kind, key, rnd.randrange(1, 6)))
    if rnd.random() < 0.7:
        out.append("bar 0 %d %s %d" % (rnd.randrange(goals),
                                       rnd.choice(("lost", "gain", "back")),
                                       rnd.choice(keys)))
    for _ in range(rnd.randrange(2, 5)):
        out.append("step")
        for _ in range(rnd.randrange(1, 3)):
            key = rnd.choice(keys)
            out.append("cut %d" % key if rnd.random() < 0.3
                       else "put %d %d" % (key, rnd.randrange(0, 6)))
        out.append("ok" if rnd.random() < 0.8 else "err")
    return out


def candidates(count):
    out = []
    for turn in range(count):
        rnd = random.Random("pick|small|%d" % turn)
        lines = small(rnd)
        if 9 <= len(lines) <= 22:
            out.append(("small", turn, lines))
    return out


def main():
    ref = lab.tree(lab.SOL)
    broken = lab.tree(lab.TASK / "environment" / "app_src" / "crd")
    trees = {}
    for name, files in rd.READINGS.items():
        room = pathlib.Path(lab.tempfile.mkdtemp(prefix="pick-"))
        for part in lab.PARTS:
            (room / part).write_text((lab.SOL / part).read_text(encoding="utf-8"),
                                     encoding="utf-8", newline="\n")
        for part, src in files.items():
            (room / part).write_text(src, encoding="utf-8", newline="\n")
        trees[name] = lab.tree(room)

    best = []
    for fam, turn, lines in candidates(int(sys.argv[1]) if len(sys.argv) > 1 else 40):
        text = "\n".join(lines) + "\n"
        want = lab.run_text(ref, text)
        if want and want[0] == "raised":
            continue
        if lab.run_text(broken, text) == want:
            continue
        marks = sum(1 for line in want if line.startswith("mark"))
        fires = sum(1 for line in want if line.startswith(("fire", "void")))
        if marks < 1:
            continue
        decided = [name for name, here in trees.items()
                   if lab.run_text(here, text) != want]
        heavy = [name for name in decided if name in HEAVY]
        best.append((len(heavy), -min(fires, 2), len(decided), len(lines),
                     fam, turn, lines, want, decided))
    best.sort(key=lambda row: row[:4])
    for row in best[:8]:
        print("heavy=%d fires=%d decided=%d lines=%d  %s-%d  decides %s"
              % (row[0], -row[1], row[2], row[3], row[4], row[5], sorted(row[8])), flush=True)
    for row in best[:2]:
        print("\n--- candidate %s-%d ---" % (row[4], row[5]), flush=True)
        print("\n".join(row[6]), flush=True)
        print("--- correct output ---", flush=True)
        print("\n".join(row[7]), flush=True)
        print("--- shipped engine prints ---", flush=True)
        print("\n".join(lab.run_text(broken, "\n".join(row[6]) + "\n")), flush=True)


if __name__ == "__main__":
    main()
