"""Re-derive every number the shipped prose quotes, from the code that decides it.

A committed harness value can disagree with every number in the prose and nothing local or
remote will notice: `publish-settle-order` shipped `PER=60` in `test.sh` against a brief, a
metadata block and a set of timings that all said 45. So the count per family comes from
`test.sh`, the population comes from `gen.programs`, and both the brief and `task.toml` are
checked against them rather than against memory.
"""
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
TASK = HERE.parent.parent / "tasks" / "claim-line-stall"
sys.path.insert(0, str(TASK / "tests"))

import cases  # noqa: E402
import gen  # noqa: E402

WORDS = {
    37: "thirty-seven", 246: "two hundred and forty-six", 277: "two hundred and seventy-seven",
    283: "283", 1600: "sixteen hundred", 3000: "three thousand", 2000: "two thousand",
    26000: "twenty-six thousand", 1500: "fifteen hundred",
}


def main():
    bad = []
    harness = (TASK / "tests" / "test.sh").read_text(encoding="utf-8")
    per = int(re.search(r"^per=(\d+)$", harness, re.M).group(1))
    wall = int(re.search(r"^wall=(\d+)$", harness, re.M).group(1))

    progs = gen.programs("counts", per)
    hand = len(cases.ORDER)
    nonce = len(progs)
    big = sum(1 for fam, _n, _l in progs if fam in ("wide", "tall"))
    total = hand + nonce
    small = total - big

    flat = lambda t: " ".join(t.split()).lower()
    brief = flat((TASK / "instruction.md").read_text(encoding="utf-8"))
    meta = flat((TASK / "task.toml").read_text(encoding="utf-8"))

    want = {
        "graded total (task.toml)": (str(total), meta),
        "hand cases (task.toml)": (WORDS[hand], meta),
        "nonce programs (task.toml)": (WORDS[nonce], meta),
        "smaller programs (brief)": (WORDS[small], brief),
        "limit (brief)": ("inside %d seconds" % wall, brief),
        "limit (task.toml)": ("%d second limit" % wall, meta),
    }
    for what, (needle, where) in want.items():
        if needle.lower() not in where:
            bad.append("%s: %r is not in the prose" % (what, needle))

    # the two wide shapes, straight out of the generator's own source
    src = (TASK / "tests" / "gen.py").read_text(encoding="utf-8")
    units, waiters, rounds = [int(x) for x in re.search(
        r"units, waiters, rounds = (\d+), (\d+), (\d+)", src).groups()]
    held, pending, cycles = [int(x) for x in re.search(
        r"held, waiters, cycles = (\d+), (\d+), (\d+)", src).groups()]
    for value, what in ((units, "wide units"), (waiters, "wide waiters"),
                        (rounds, "wide rounds"), (pending, "tall waiters"),
                        (cycles, "tall cycles")):
        word = WORDS.get(value)
        if word is None or word.lower() not in brief:
            bad.append("%s = %d: %r is not in the brief" % (what, value, word))

    print("per=%d wall=%d -> %d hand + %d nonce = %d graded, %d of them wide or tall"
          % (per, wall, hand, nonce, total, big))
    print("wide: %d units, %d asks, %d rounds | tall: %d held, %d asks, %d cycles"
          % (units, waiters, rounds, held, pending, cycles))
    for one in bad:
        print("   MISMATCH %s" % one)
    print("every quoted number is re-derived" if not bad else "%d mismatch(es)" % len(bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
