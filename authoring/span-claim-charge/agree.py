"""Reference against the sealed model over the generated population, plus family statistics.

Counts, per family, how many family questions each program asks, how many drops of a line that
had stamps it makes (the re-parenting case), and how long the traces are - the numbers that say
whether a family is shaped for the readings it exists for, or whether it is only hoping.
"""
import pathlib
import sys
import tempfile
import time

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lab  # noqa: E402

sys.path.insert(0, str(lab.TASK / "tests"))
sys.path.insert(0, str(lab.TASK / "tests" / "seal"))
import cases  # noqa: E402
import gen  # noqa: E402
import model  # noqa: E402


def stats(lines):
    """Family questions, drops that re-parent something, and errors, read off the program."""
    up = {}
    kids = {}
    fams = 0
    reparent = 0
    for row in lines:
        w = row.split()
        if not w:
            continue
        if w[0] == "n":
            up[w[1]] = None
        elif w[0] == "p":
            up[w[2]] = w[1]
            kids.setdefault(w[1], set()).add(w[2])
        elif w[0] == "d":
            if kids.get(w[1]):
                reparent += 1
                for k in kids[w[1]]:
                    up[k] = up.get(w[1])
                    if up[k] is not None:
                        kids.setdefault(up[k], set()).add(k)
            kids.pop(w[1], None)
            up.pop(w[1], None)
        elif w[0] == "u":
            fams += 1
    return fams, reparent


def main():
    seed = sys.argv[1] if len(sys.argv) > 1 else "probe"
    per = int(sys.argv[2]) if len(sys.argv) > 2 else 12
    only = sys.argv[3] if len(sys.argv) > 3 else None
    over = sys.argv[4] if len(sys.argv) > 4 else None
    ref = lab.tree(lab.TASK / "solution", over)
    for name in cases.ORDER:
        if lab.drive(ref, cases.ops(name)) != model.expect(cases.ops(name)):
            print("HAND CASE DIFFERS: %s" % name, flush=True)
    tally = {}
    bad = []
    for fam, name, lines in gen.programs(seed, per):
        if only and fam != only:
            continue
        t0 = time.time()
        want = model.expect(lines)
        tm = time.time() - t0
        row = tally.setdefault(fam, [0, 0, 0, 0, 0.0, 0.0])
        fams, reparent = stats(lines)
        row[0] += 1
        row[1] += fams
        row[2] += reparent
        row[3] += len(want)
        row[4] += tm
        t0 = time.time()
        got = lab.drive(ref, lines, timeout=900)
        row[5] += time.time() - t0
        if got != want:
            first = next((i for i, (a, b) in enumerate(zip(got, want)) if a != b), None)
            bad.append((name, first, got[first:first + 1] if first is not None else got[-1:],
                        want[first:first + 1] if first is not None else want[-1:]))
    print("%-7s %5s %7s %8s %8s %8s %8s" % ("family", "progs", "u-asks", "reparent", "lines",
                                            "model-s", "ref-s"), flush=True)
    for fam in sorted(tally):
        row = tally[fam]
        print("%-7s %5d %7d %8d %8d %8.1f %8.1f" % (fam, row[0], row[1], row[2], row[3],
                                                    row[4], row[5]), flush=True)
    print("\n%d disagreements" % len(bad), flush=True)
    for row in bad[:6]:
        print("   ", row, flush=True)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
