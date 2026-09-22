"""Re-derive every count and bound the brief states from the code, not from memory
(CLAUDE.md: counts drift with the generator). Run after any change to gen.py, cases.py,
test.sh or instruction.md; exits 1 on any disagreement.

    python3 authoring/journal-gap-mend/counts.py [seeds...]
"""
import pathlib
import re
import sys

sys.dont_write_bytecode = True  # never leave __pycache__ inside the bundle

HERE = pathlib.Path(__file__).resolve().parent
TASK = HERE.parents[1] / "tasks" / "journal-gap-mend"
sys.path.insert(0, str(TASK / "tests" / "seal"))

import cases  # noqa: E402
import gen  # noqa: E402


def per_family():
    text = (TASK / "tests" / "test.sh").read_text()
    return int(re.search(r"^PER_FAMILY=(\d+)$", text, re.M).group(1))


def run(seed, per):
    """Every generated journal of one seed, with the true lost-entry count of each span and
    its number of entries, recorded as text_of builds it."""
    seen = []
    real = gen.text_of

    def spy(cfg, ev, spans, auds):
        seen.append((cfg, len(ev), [s1 - s0 for s0, s1 in spans], set(auds)))
        return real(cfg, ev, spans, auds)
    gen.text_of = spy
    try:
        progs = gen.programs(seed, per)
    finally:
        gen.text_of = real
    return progs, seen


def main(argv):
    seeds = argv or ["counts-a", "counts-b", "counts-c"]
    per = per_family()
    brief = (TASK / "instruction.md").read_text()
    bad = []

    def check(ok, what):
        print("   %-4s %s" % ("ok" if ok else "BAD", what))
        if not ok:
            bad.append(what)

    hand = len(cases.ORDER)
    for seed in seeds:
        progs, seen = run(seed, per)
        print("== seed %s" % seed)
        gen_n = len(progs)
        busy = [s for (f, _n, _t), s in zip(progs, seen) if f == "busy"]
        rest = [s for (f, _n, _t), s in zip(progs, seen) if f != "busy"]
        check(gen_n == (len(gen.FAMILIES) - 1) * per + gen.BUSY_COUNT,
              "generated journals: %d" % gen_n)
        check(all(max(s[2] or [0]) <= 5 for s in rest), "non-busy spans hold at most 5 entries")
        long_ = [s for s in rest if 36 <= s[1] <= 44]
        check(len(long_) == 30 and all(not s[3] for s in long_),
              "journals of 36-44 entries: %d, none with an audit before the last line" % len(long_))
        check(all(s[1] < 36 for s in rest if s not in long_), "every other journal is shorter")
        check(len(busy) == 4 and all(len(s[2]) == 1 and 12 <= s[2][0] <= 14 for s in busy),
              "busy: %d journals, one span of %s entries" % (len(busy), [s[2] for s in busy]))
        check(all(s[0][0] <= 4 and s[0][1] <= 5 and 1 <= s[0][2] <= 3 for s in seen),
              "at most four locks, five sessions, K from 1 to 3")
    print("== the brief")
    check("%d journals written by hand" % hand in brief, "hand journals: %d" % hand)
    total = hand + (len(gen.FAMILIES) - 1) * per + gen.BUSY_COUNT
    check("%d generated after you finish" % (total - hand) in brief, "generated: %d" % (total - hand))
    check("All %d have to finish" % total in brief, "total: %d" % total)
    check("In %d of them no lost stretch" % (total - gen.BUSY_COUNT) in brief,
          "journals with no span over 5: %d" % (total - gen.BUSY_COUNT))
    small = (TASK / "environment" / "app_src" / "journals" / "small.txt").read_text()
    check(small.strip() == cases.text("small").strip(), "journals/small.txt is the hand journal 'small'")
    print("%d disagreement(s)" % len(bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
