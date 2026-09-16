"""Every correct variant scores exactly the reference over the population, and the readings do not."""
import pathlib
import sys

import lab

TASK = lab.TASK
sys.path.insert(0, str(TASK / "tests"))
sys.path.insert(0, str(TASK / "tests" / "seal"))
import gen     # noqa: E402
import model   # noqa: E402

VAR = pathlib.Path(__file__).resolve().parent / "variants"


def drive(here, lines):
    ops, prog, store = lab.load(here)
    f = store.Fld()
    for w in prog.walk(lines):
        ops.ex(f, w)
    return f.out


def main():
    per = int(sys.argv[1]) if len(sys.argv) > 1 else 60
    work = [(f, n, l) for f, n, l in gen.programs("var", per) if f not in ("wide", "deep")]
    want = {n: model.expect(l) for _f, n, l in work}
    ok = True
    for d in sorted(VAR.iterdir()):
        if not d.is_dir():
            continue
        here = lab.tree(d)
        bad = sum(1 for _f, n, l in work if drive(here, l) != want[n])
        print("%-8s %d of %d disagree with the reference" % (d.name, bad, len(work)))
        ok = ok and bad == 0
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
