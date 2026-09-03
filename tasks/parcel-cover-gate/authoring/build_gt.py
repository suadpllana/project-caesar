"""Write tests/gt.json, and refuse to write one that has not been proved.

Three things have to hold before a byte is written. The reference has to agree
with the sealed second reading on every named feed. It has to agree with it on a
long run of feeds neither of them has seen. And the shipped tree has to disagree
with it on the named feeds, because a ground truth the broken tree already
satisfies is a ground truth that grades nothing.

Line endings are forced to LF explicitly. `Path.write_text` opens in text mode,
which on some hosts turns every newline into a pair, and a gt.json full of them
ships an archive the structural check rejects for a reason nobody can see.
"""

import json
import pathlib
import sys
import tempfile

import fuzz
import lab

OUT = lab.ROOT / "tests" / "gt.json"


def main(argv):
    rounds = int(argv[1]) if len(argv) > 1 else 600
    feeds = lab.named()
    hold = tempfile.mkdtemp(prefix="pcg-gt-")
    got = lab.play(lab.tree(hold + "/ref", lab.reference()), feeds)
    want = lab.second(feeds)

    off = [n for n in sorted(feeds) if got[n] != want[n]]
    if off:
        print("the two readings disagree on: %s" % ", ".join(off))
        return 1

    bad, many, rows = fuzz.run(rounds, nonce="gtproof")
    if bad:
        print("the two readings disagree on generated feeds: %s" % bad[:6])
        return 1
    print("proved on %d feeds, %d rows" % (many, rows))

    ship = lab.play(lab.tree(hold + "/ship", lab.shipped()), feeds)
    same = [n for n in sorted(feeds) if ship[n] == got[n]]
    print("the shipped tree already matches on %d of %d named feeds"
          % (len(same), len(feeds)))
    if len(same) == len(feeds):
        print("nothing here grades anything")
        return 1

    blob = json.dumps(got, sort_keys=True, indent=1) + "\n"
    with open(OUT, "w", newline="\n") as fh:
        fh.write(blob)
    print("wrote %s (%d feeds, %d bytes)" % (OUT, len(got), len(blob)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
