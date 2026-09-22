"""Run every correct variant under authoring/feed-lag-pare/variants against the model.

A stated-contract implementation that scores 0 is verifier overfitting, so the variants are
checked the same way the submission is: the hand cases, a random population and the generated
population, compared line for line against the sealed model. The wall clock is checked too,
because a variant that is correct and does not finish is graded exactly like a wrong one.

    python authoring/feed-lag-pare/variant_check.py [per]
"""
import pathlib
import random
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lab  # noqa: E402
import readings  # noqa: E402

cases, gen, model = lab.sealed()
VARIANTS = sorted(p for p in (HERE / "variants").iterdir() if p.is_dir())


def main():
    per = int(sys.argv[1]) if len(sys.argv) > 1 else 40
    work = [(name, cases.prog(name)) for name in cases.ORDER]
    work += [(name, text.splitlines()) for name, text in readings.generated(300)]
    population = gen.programs("variant", per)
    bad = 0
    for vdir in VARIANTS:
        here = lab.tree(vdir)
        wrong = []
        for name, lines in work:
            if lab.run_text(here, "\n".join(lines) + "\n") != model.expect(lines):
                wrong.append(name)
        start = time.time()
        for _fam, name, lines in population:
            if lab.run_text(here, "\n".join(lines) + "\n") != model.expect(lines):
                wrong.append(name)
        took = time.time() - start
        print("%-10s %4d checked, %4d graded in %.1fs, %d wrong %s"
              % (vdir.name, len(work), len(population), took, len(wrong), wrong[:3]),
              flush=True)
        bad += len(wrong)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
