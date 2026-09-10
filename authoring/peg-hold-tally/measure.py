"""How much of the population each wrong reading moves, and which hand case names it.

readingcheck answers "is it separated at all"; this answers "by how much", which is the number
that matters under all-or-nothing grading: a reading that moves one program in a hundred still
scores zero, and a reading that moves none is untested.
"""
import sys

import readings as book

sys.path.insert(0, str(book.TASK / "tests"))

import cases  # noqa: E402


def main():
    rounds = int(sys.argv[1]) if len(sys.argv) > 1 else 300
    hand = book.enumerated()
    made = book.generated(rounds)
    want_hand = [book.run(book.REFERENCE, text) for _n, text in hand]
    want_made = [book.run(book.REFERENCE, text) for _n, text in made]
    print("%-16s %9s %11s   %s" % ("reading", "hand", "generated", "first hand case"))
    bad = []
    for name in sorted(book.READINGS):
        alt = book.policy(name)
        h = [hand[i][0] for i in range(len(hand))
             if book.run(alt, hand[i][1]) != want_hand[i]]
        g = [i for i in range(len(made)) if book.run(alt, made[i][1]) != want_made[i]]
        print("%-16s %4d/%-4d %5d/%-5d  %s"
              % (name, len(h), len(hand), len(g), len(made), h[0] if h else "-"))
        if not h:
            bad.append("%s: no enumerated case names it" % name)
        if not g:
            bad.append("%s: moves none of the generated population" % name)
    for line in bad:
        print("FINDING", line)
    return 1 if bad else 0


sys.exit(main())
