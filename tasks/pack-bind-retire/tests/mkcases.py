"""Write the graded scripts into one directory.

The enumerated ones are fixed and were written by hand, each shrunk to the shortest script
that separates one wrong reading. The rest are built from the nonce, which is made after the
agent has finished, so nothing in the submitted tree can have been fitted to them.
"""
import argparse
import os

import cases
import gen


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--nonce", required=True)
    ap.add_argument("--count", type=int, default=300)
    ap.add_argument("--into", required=True)
    a = ap.parse_args()
    os.makedirs(a.into, exist_ok=True)
    for nm in sorted(cases.FIXED):
        with open(os.path.join(a.into, nm + ".txt"), "w", encoding="ascii") as fh:
            fh.write(cases.FIXED[nm])
    gen.build(a.nonce, a.count, a.into)
    print("wrote %d enumerated and %d generated scripts" % (len(cases.FIXED), a.count))


if __name__ == "__main__":
    main()
