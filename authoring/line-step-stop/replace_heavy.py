"""Rebuild one heavy session in heavy.json from its own seed.

    python replace_heavy.py INDEX SEED

Used for index 11, built before forge.heavy_session capped the tape at 20000 values (it
carried 560,583), and for index 12, which executed 31.7M instructions in all against
sample-long's 22.6M - the brief says long is as heavy as the heaviest session graded, so no
heavy session may exceed it on either count. Every other entry is left exactly as
make_heavy.py wrote it.
"""
import json
import os
import random
import sys
import time

from lab import forge, HERE

FLOOR = 3000000
# sample-long, measured with volume.split: the ceiling on both counts.
LONG_IN_FRAME = 14984670
LONG_TOTAL = 22649734


def main():
    idx, seed = int(sys.argv[1]), int(sys.argv[2])
    path = os.path.join(HERE, "heavy.json")
    heavy = json.load(open(path))
    rng = random.Random(seed)
    t = time.time()
    while True:
        try:
            s = forge.heavy_session(rng, heavy_range=(250000, 700000), floor=FLOOR, tries=30)
        except RuntimeError:
            continue
        if s["volume"] <= LONG_TOTAL and s["in_frame"] <= LONG_IN_FRAME:
            break
    assert len(s["tape"]) <= 20000, len(s["tape"])
    old = heavy[idx]
    heavy[idx] = s
    text = json.dumps(heavy)
    with open(path, "w", newline="\n") as f:
        f.write(text)
    print("heavy index %d: tape %d -> %d, volume %d in-frame %d cmds %d image %d lines  %.0fs" % (
        idx, len(old["tape"]), len(s["tape"]), s["volume"], s["in_frame"], len(s["cmds"]),
        len(s["image"].splitlines()), time.time() - t), flush=True)


if __name__ == "__main__":
    main()
