"""Measure every wrong reading: what it moves, and which enumerated case catches it.

A reading no hand case catches is a rule whose failure would not name itself. A reading that
moves nothing is a distinction the population does not exercise, and with all-or-nothing grading
the nonce set would still catch it - but only by luck, so that is reported too. A reading that
crashes is not a reading at all: it is a patch that did not apply the way it reads.
"""
import sys

import lab
import make_readings

T = lab.ROOT / "tasks" / "claim-stand-break" / "tests"
sys.path.insert(0, str(T))
import cases  # noqa: E402
import gen  # noqa: E402

SOL = lab.ROOT / "tasks" / "claim-stand-break" / "solution"


def main(argv):
    per = int(argv[1]) if len(argv) > 1 else 12
    work = [(f, n, l) for f, n, l in gen.programs("r1", per) if f not in ("deep", "wide")]
    texts = ["\n".join(l) + "\n" for _f, _n, l in work]
    hand = ["\n".join(cases.prog(n)) + "\n" for n in cases.ORDER]
    ok_room = lab.tree(SOL)
    want_pop = lab.batch(ok_room, texts)
    want_hand = lab.batch(ok_room, hand)
    print("%-14s %6s  %-22s %s" % ("reading", "moves", "case named", "caught by"))
    bad = []
    for name, _reads, case, _patch in make_readings.READINGS:
        room = lab.tree(make_readings.OUT / name)
        got_pop = lab.batch(room, texts)
        got_hand = lab.batch(room, hand)
        broke = [n for n, out in zip(cases.ORDER, got_hand)
                 if any(line.startswith("!!") for line in out)]
        moved = sum(1 for a, b in zip(want_pop, got_pop) if a != b)
        caught = [n for n, a, b in zip(cases.ORDER, want_hand, got_hand) if a != b]
        print("%-14s %5.1f%%  %-22s %s" % (name, 100.0 * moved / len(texts), case,
                                           ", ".join(caught[:4]) or "NOTHING"))
        if broke:
            bad.append((name, "the reading crashed on %s" % broke[0], caught))
        if case not in caught:
            bad.append((name, case, caught))
        if not moved:
            bad.append((name, "moves nothing in the population", caught))
    print()
    for name, case, caught in bad:
        print("FAIL %s: %s; caught by %s" % (name, case, caught or "nothing"))
    print("%d readings, %d findings" % (len(make_readings.READINGS), len(bad)))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
