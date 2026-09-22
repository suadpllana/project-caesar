"""Every correct variant has to print exactly what the reference prints, on the whole set."""
import pathlib
import sys

import lab

T = lab.ROOT / "tasks" / "claim-stand-break" / "tests"
sys.path.insert(0, str(T))
import cases  # noqa: E402
import gen  # noqa: E402

HERE = pathlib.Path(__file__).resolve().parent
VARIANTS = ("ok-seal", "slow-walk", "slow-over", "slow-sort", "slow-answer")


def main(argv):
    per = int(argv[1]) if len(argv) > 1 else 12
    skip = argv[2:] or []
    work = [(f, n, l) for f, n, l in gen.programs("v1", per) if f not in ("deep", "wide")]
    texts = ["\n".join(l) + "\n" for _f, _n, l in work]
    texts += ["\n".join(cases.prog(n)) + "\n" for n in cases.ORDER]
    want = lab.batch(lab.tree(lab.ROOT / "tasks" / "claim-stand-break" / "solution"), texts)
    bad = 0
    for tag in VARIANTS:
        if tag in skip:
            continue
        got = lab.batch(lab.tree(HERE / "variants" / tag), texts, seconds=3600)
        off = [i for i, (a, b) in enumerate(zip(want, got)) if a != b]
        print("%-12s %s" % (tag, "matches on all %d" % len(texts) if not off
                            else "DIFFERS on %d, first %s" % (len(off), off[0])))
        bad += len(off)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
