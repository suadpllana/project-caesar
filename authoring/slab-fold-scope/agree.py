"""Reference against the sealed model over the generated population, plus family statistics.

Counts, per family, how often a fold met a slab holding both eras (the second attempt), how
often a proposal was void, and how long the traces are - the numbers that say whether a family
is shaped for the reading it exists for, or whether it is only hoping.
"""
import pathlib
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lab  # noqa: E402

sys.path.insert(0, str(lab.TASK / "tests"))
sys.path.insert(0, str(lab.TASK / "tests" / "seal"))
import gen  # noqa: E402
import model  # noqa: E402

HITS = {"again": 0, "pack": 0}
_repack = model.repack


def counting(host, b, lo, hi, base, jr):
    try:
        got = _repack(host, b, lo, hi, base, jr)
    except model.Again:
        HITS["again"] += 1
        raise
    if got:
        HITS["pack"] += 1
    return got


model.repack = counting


def main():
    seed = sys.argv[1] if len(sys.argv) > 1 else "probe"
    per = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    only = sys.argv[3] if len(sys.argv) > 3 else None
    over = sys.argv[4] if len(sys.argv) > 4 else None
    room = pathlib.Path(tempfile.mkdtemp(prefix="sfs-gen-"))
    ref = lab.tree(lab.TASK / "solution", over)
    sys.path.insert(0, str(lab.TASK / "tests"))
    import cases
    for name in cases.ORDER:
        prog = room / ("hand-%s.txt" % name)
        prog.write_text("\n".join(cases.ops(name)) + "\n", encoding="utf-8", newline="\n")
        if lab.run(ref, prog) != model.expect(cases.ops(name)):
            print("HAND CASE DIFFERS: %s" % name, flush=True)
        prog.unlink()
    tally = {}
    bad = []
    for fam, name, lines in gen.programs(seed, per):
        if only and fam != only:
            continue
        HITS["again"] = HITS["pack"] = 0
        want = model.expect(lines)
        row = tally.setdefault(fam, [0, 0, 0, 0, 0])
        row[0] += 1
        row[1] += HITS["again"]
        row[2] += HITS["pack"]
        row[3] += sum(1 for line in want if line.startswith("void"))
        row[4] += len(want)
        prog = room / ("%s.txt" % name)
        prog.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
        got = lab.run(ref, prog, timeout=900)
        if got != want:
            first = next((i for i, (a, b) in enumerate(zip(got, want)) if a != b), None)
            bad.append((name, first, got[first:first + 1], want[first:first + 1]))
        prog.unlink()
    print("%-9s %6s %7s %6s %6s %8s" % ("family", "progs", "retries", "packs", "voids", "lines"),
          flush=True)
    for fam in sorted(tally):
        row = tally[fam]
        print("%-9s %6d %7d %6d %6d %8d" % (fam, row[0], row[1], row[2], row[3], row[4]),
              flush=True)
    print("\n%d disagreements" % len(bad), flush=True)
    for row in bad[:6]:
        print("   ", row, flush=True)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
