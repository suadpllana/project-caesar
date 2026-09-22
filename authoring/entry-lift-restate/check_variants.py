import pathlib as _pl, sys as _sys, time
_sys.path.insert(0, str(_pl.Path(__file__).resolve().parent.parent.parent / "tasks" / "entry-lift-restate" / "tests"))
"""Every correct variant against the specification and the two scale families."""
import random
import sys

import cases
import gen
import lab
import naive

VAR = _pl.Path(__file__).resolve().parent / "variants"


def main(argv):
    per = int(argv[1]) if len(argv) > 1 else 12
    bad = 0
    for d in sorted(VAR.iterdir()):
        if not d.is_dir():
            continue
        eng = lab.loader(lab.build(d))
        wrong = []
        for name in cases.ORDER:
            text = "\n".join(cases.prog(name)) + "\n"
            if eng.run(text) != naive.run(text):
                wrong.append(name)
        for fam, name, lines in gen.programs("variant-seed", per):
            if fam in ("wide", "deep"):
                continue
            text = "\n".join(lines) + "\n"
            if eng.run(text) != naive.run(text):
                wrong.append(name)
        secs = 0.0
        for fam, fn in gen.BIG:
            for k in range(gen.BIG_EACH):
                rng = random.Random("variant/%s/%d" % (fam, k))
                text = "\n".join(fn(rng, gen.BIG_SIZE)) + "\n"
                t0 = time.perf_counter()
                eng.run(text)
                secs += time.perf_counter() - t0
        print("%-10s %s   six scale programs in %.2fs"
              % (d.name, "agrees everywhere" if not wrong else "WRONG: %s" % wrong[:4], secs),
              flush=True)
        bad += bool(wrong)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
