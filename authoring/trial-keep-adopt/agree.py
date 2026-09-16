"""Reference against the sealed model, over the generated population.

They are written apart - the reference recurses and takes each read where the form's code takes
it, the model drives an explicit stack and asks a form what it would read next - so agreement on
a shaped population is evidence that the contract, and not one implementation, is what is graded.
"""
import pathlib
import sys
import time

import lab

TASK = lab.TASK
sys.path.insert(0, str(TASK / "tests"))
sys.path.insert(0, str(TASK / "tests" / "seal"))
import gen      # noqa: E402
import model    # noqa: E402


def main():
    per = int(sys.argv[1]) if len(sys.argv) > 1 else 40
    seed = sys.argv[2] if len(sys.argv) > 2 else "agree"
    skip = {"wide", "deep"} if len(sys.argv) <= 3 else set()
    here = lab.ref()
    ops, prog, store = lab.load(here)
    bad, n = [], 0
    t0 = time.time()
    for fam, name, lines in gen.programs(seed, per):
        if fam in skip:
            continue
        f = store.Fld()
        for w in prog.walk(lines):
            ops.ex(f, w)
        want = model.expect(lines)
        n += 1
        if f.out != want:
            bad.append((name, f.out, want))
    print("%d programs, %d disagreements, %.1fs" % (n, len(bad), time.time() - t0))
    for name, got, want in bad[:3]:
        print("==", name)
        for i, (a, b) in enumerate(zip(got + [""] * 9, want + [""] * 9)):
            if a != b:
                print("   line %d: reference %r model %r" % (i, a, b))
                break
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
