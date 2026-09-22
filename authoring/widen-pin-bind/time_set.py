"""Time a whole graded set under one directory of the six files.

The limit in the brief is for the set, so the number that matters is the total over the
thirty-two enumerated programs and everything the generator makes at the graded family size.
Output is flushed: a harness whose output sits in a buffer behind the slow case looks exactly
like a hang.
"""
import pathlib
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lab  # noqa: E402

cases, gen, _model = lab.sealed()


def main():
    which = sys.argv[1] if len(sys.argv) > 1 else str(lab.SOL)
    per = int(sys.argv[2]) if len(sys.argv) > 2 else 40
    work = [("hand", n, cases.prog(n)) for n in cases.ORDER] + gen.programs("timing", per)
    engine = lab.engine(which)
    worst = (0.0, "")
    whole = 0.0
    for fam, name, lines in work:
        text = "\n".join(lines) + "\n"
        t0 = time.time()
        out = engine.run(text)
        took = time.time() - t0
        whole += took
        if took > worst[0]:
            worst = (took, name)
        if out and out[0] in ("DIED", "RAISED"):
            print("  %s: %s" % (name, out[0]), flush=True)
    print("%-52s %d programs, %.2f s total, worst %s at %.2f s"
          % (pathlib.Path(which).name, len(work), whole, worst[1], worst[0]), flush=True)


if __name__ == "__main__":
    main()
