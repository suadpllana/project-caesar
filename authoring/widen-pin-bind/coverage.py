"""How much of the generated population each wrong reading actually moves.

A reading separated by one enumerated case is a reading a submission can only fail on that one
program, and all-or-nothing grading makes that indistinguishable from bad luck. The number
below is the fraction of generated programs whose record differs - the pressure the population
itself puts on that rule. A reading near zero means the families are not shaped for it.

    python3 -u authoring/widen-pin-bind/coverage.py [per-family]
"""
import pathlib
import random
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import emit  # noqa: E402
import lab  # noqa: E402

cases, gen, _model = lab.sealed()


def main():
    per = int(sys.argv[1]) if len(sys.argv) > 1 else 12
    emit.build_all()
    work = []
    for fam, big in gen.FAMILIES:
        if big:
            continue
        for i in range(per):
            rng = random.Random("coverage|%s|%d" % (fam, i))
            work.append("\n".join(gen.build(fam, rng)) + "\n")
    want = [lab.run_text(lab.SOL, text) for text in work]
    rows = []
    for name, files in sorted(emit.READINGS.items()):
        room = lab.tree(lab.SOL)
        for part, src in files.items():
            (room / "res" / part).write_text(src, encoding="utf-8")
        moved = sum(1 for text, ref in zip(work, want)
                    if lab.Engine(room).run(text) != ref)
        rows.append((moved / len(work), name, moved))
    rows.sort()
    for frac, name, moved in rows:
        print("%-24s %5.1f%%  %d of %d" % (name, 100 * frac, moved, len(work)))
    print("\nthinnest: %s at %.1f%%" % (rows[0][1], 100 * rows[0][0]))


if __name__ == "__main__":
    main()
