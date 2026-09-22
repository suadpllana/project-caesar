"""Time one implementation over the whole generated population.

Output is the measurement, so everything flushes (CLAUDE.md: stdout buffering looks exactly
like a hang).
"""
import sys
import time
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import gen   # noqa: E402
import lab   # noqa: E402


def place(name):
    """Correct variants live under variants/, the naive-but-correct ones under slow/."""
    if name.startswith("slow-"):
        return HERE / "slow" / name[5:]
    return HERE / "variants" / name


def main():
    which = sys.argv[1]
    per = int(sys.argv[2]) if len(sys.argv) > 2 else 40
    seed = sys.argv[3] if len(sys.argv) > 3 else "timing"
    over = lab.TASK / "solution" if which == "reference" else place(which)
    run = lab.loader(lab.tree(over))
    per_fam = {}
    whole = time.time()
    for fam, _name, lines in gen.programs(seed, per):
        text = "\n".join(lines) + "\n"
        one = time.time()
        run(text)
        per_fam[fam] = per_fam.get(fam, 0.0) + time.time() - one
    total = time.time() - whole
    for fam in sorted(per_fam, key=lambda f: -per_fam[f]):
        print("  %-8s %7.2fs" % (fam, per_fam[fam]), flush=True)
    print("%-14s TOTAL %7.2fs" % (which, total), flush=True)


if __name__ == "__main__":
    main()
