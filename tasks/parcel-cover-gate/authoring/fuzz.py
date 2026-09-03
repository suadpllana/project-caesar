"""The reference against the sealed second reading, on feeds nobody wrote.

`build_gt.py` will not write an answer file without a clean run of this. Two
implementations that share no code agreeing on tens of thousands of rows is the
only evidence anybody has that what ships is the rules rather than one author's
habits, and it is the check that would have caught every ground-truth mistake
this repo has ever made.

    python3 authoring/fuzz.py [rounds]
"""

import json
import sys
import tempfile

import lab


def run(rounds, nonce="fuzz"):
    feeds = lab.made(nonce, rounds)
    feeds.update(lab.named())
    hold = tempfile.mkdtemp(prefix="pcg-fuzz-")
    got = lab.play(lab.tree(hold + "/ref", lab.reference()), feeds)
    want = lab.second(feeds)
    bad = [n for n in sorted(feeds) if got[n] != want[n]]
    rows = sum(len(got[n]["rows"]) for n in got)
    return bad, len(feeds), rows


def main(argv):
    rounds = int(argv[1]) if len(argv) > 1 else 800
    bad, many, rows = run(rounds)
    print("%d feeds, %d rows" % (many, rows))
    if bad:
        print("MISMATCH on %d: %s" % (len(bad), ", ".join(bad[:6])))
        return 1
    print("the reference and the second reading agree everywhere")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
