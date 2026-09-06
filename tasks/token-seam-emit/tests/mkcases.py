"""Write the graded requests.

Run by root, after the agent has finished, from a nonce made in `test.sh`. Three families
land in the same directory and the run cannot tell them apart:

  h*  the enumerated requests, one per decision, from `cases.py`
  g*  three hundred generated requests
  w*  the wide family, which is where an implementation whose per-step cost grows with the
      length of the request so far stops fitting in the run's wall clock
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cases
import gen

# The wide family is what the run's wall clock is for. It is fixed at eight in the
# verifier; the authoring sweeps set TSE_WIDE lower when they are measuring something other
# than the resource gate, and say so when they do.
WIDE = int(os.environ.get("TSE_WIDE", "8"))
NARROW = 300


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--nonce", required=True)
    ap.add_argument("--into", required=True)
    a = ap.parse_args()

    os.makedirs(a.into, exist_ok=True)
    for name, spec in cases.CASES:
        gen.write(spec, os.path.join(a.into, "h_" + name + ".txt"))
    for name, spec in gen.make(a.nonce, NARROW, tag="g"):
        gen.write(spec, os.path.join(a.into, name + ".txt"))
    for name, spec in gen.make(a.nonce + ":w", WIDE, wide=True, tag="w"):
        gen.write(spec, os.path.join(a.into, name + ".txt"))

    n = len([f for f in os.listdir(a.into) if f.endswith(".txt")])
    print("wrote %d requests" % n)
    if n != len(cases.CASES) + NARROW + WIDE:
        raise SystemExit("request count is wrong: %d" % n)


if __name__ == "__main__":
    main()
