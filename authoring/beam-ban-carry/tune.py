"""Try a wide/churn shape against every implementation and print the seconds each takes."""
import pathlib
import random
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import gen   # noqa: E402
import lab   # noqa: E402


def place(name):
    """Correct variants live under variants/, the naive-but-correct ones under slow/."""
    if name.startswith("slow-"):
        return HERE / "slow" / name[5:]
    return HERE / "variants" / name

WHO = ["reference", "var-b", "var-a", "slow-lent", "slow-rebuild", "slow-scan"]


def build(kind, v, cfg, deg, smax, stops, asks, i):
    rng = random.Random("tune|%s|%d" % (kind, i))
    rows = gen._edges(rng, v, deg, smax) + gen._stops(rng, v, stops, smax)
    return "\n".join(gen._text(cfg, rows, gen._prompts(rng, v, asks, 2, 4), rng)) + "\n"


def main():
    kind = sys.argv[1]
    spec = eval(sys.argv[2])          # (v, cfg, deg, smax, stops, asks)
    who = sys.argv[3:] or WHO
    texts = [build(kind, *spec, i) for i in range(3)]
    base = None
    for name in who:
        over = lab.TASK / "solution" if name == "reference" else place(name)
        run = lab.loader(lab.tree(over))
        t = time.time()
        outs = [run(text) for text in texts]
        took = time.time() - t
        if base is None:
            base = outs
            extra = "halts %s lines %d" % (
                sorted({l.split()[2] for o in outs for l in o if l.startswith("halt")}),
                sum(len(o) for o in outs))
        else:
            extra = "same as reference" if outs == base else "*** DIFFERS ***"
        print("  %-13s %7.2fs  %s" % (name, took, extra), flush=True)


if __name__ == "__main__":
    main()
