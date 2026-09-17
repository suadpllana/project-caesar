"""Search for the worked example, rather than choosing one.

The brief has to print one record of one program verbatim, or a format slip fails every case for
a reason that is not the task. That published line is evidence, and evidence decides readings: an
example that rules out six of the wrong readings has handed over six rules. So every candidate is
scored by how many of the readings in emit.py disagree with the model on the line the brief would
quote, and the smallest program with the fewest is the one that ships.
"""
import itertools
import pathlib
import random
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent.parent / "tasks/queue-hold-drop/tests"))
sys.path.insert(0, str(HERE.parent.parent / "tasks/queue-hold-drop/tests/seal"))
import emit  # noqa: E402
import gen  # noqa: E402
import lab  # noqa: E402
import model  # noqa: E402

SHIPPED = lab.tree()
TREES = {name: lab.tree(None) for name in ()}
SHAPES = ("out", "ack", "gone", "idle", "rec", "row", "none")


def reading_trees():
    out = {}
    for name, files in emit.BUILT.items():
        room = lab.tree(lab.TASK / "solution")
        for part, src in files.items():
            (room / "pend" / part).write_text(src, encoding="utf-8", newline="\n")
        out[name] = room
    return out


def candidates(n=900):
    seen = set()
    small = [fam for fam, big in gen.FAMILIES if not big]
    for i in range(n):
        fam = small[i % len(small)]
        r = random.Random("example|%s|%d" % (fam, i))
        lines = gen.build(fam, r, small=True)
        if len(lines) > 16:
            continue
        key = "\n".join(lines)
        if key in seen:
            continue
        seen.add(key)
        yield fam, lines


def main():
    trees = reading_trees()
    best = []
    for fam, lines in candidates():
        want = model.expect(lines)
        if len(want) < 4:
            continue
        got = lab.drive(SHIPPED, lines)
        wrong = [i for i in range(min(len(got), len(want))) if got[i] != want[i]]
        if not wrong:
            continue
        shapes = {line.split()[0] for line in want}
        at = wrong[0]
        decides = 0
        for name, room in trees.items():
            alt = lab.drive(room, lines)
            if at >= len(alt) or alt[at] != want[at]:
                decides += 1
        best.append((decides, len(lines), len(shapes), fam, at, lines, want, got))
    best.sort(key=lambda row: (row[0], -row[2], row[1]))
    for decides, size, shapes, fam, at, lines, want, got in best[:6]:
        print("== %s  decides %d readings, %d lines, %d shapes, wrong at line %d"
              % (fam, decides, size, shapes, at))
        for line in lines:
            print("   | %s" % line)
        print("   shipped: %s" % got[at])
        print("   right  : %s" % want[at])
        print("   whole  : %s" % want)
    print("%d candidates scored" % len(best))


if __name__ == "__main__":
    main()
