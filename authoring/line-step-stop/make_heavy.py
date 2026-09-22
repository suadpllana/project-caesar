"""Build the frozen heavy sessions: each crosses >= FLOOR instructions inside a stepping
frame, so an engine that single-steps its own frame pays one round trip per instruction.
Writes heavy.json. Slow on purpose: the model single-steps every instruction."""
import json
import os
import random
import sys
import time

from lab import forge, HERE

N = int(sys.argv[1]) if len(sys.argv) > 1 else 24
FLOOR = int(sys.argv[2]) if len(sys.argv) > 2 else 3000000
rng = random.Random(24601)
out = []
t = time.time()
while len(out) < N:
    try:
        s = forge.heavy_session(rng, heavy_range=(250000, 700000), floor=FLOOR, tries=30)
    except RuntimeError:
        continue
    out.append(s)
    print("heavy %2d: volume %8d in-frame %8d cmds %2d image %3d lines  %.0fs" % (
        len(out), s["volume"], s["in_frame"], len(s["cmds"]), len(s["image"].splitlines()),
        time.time() - t), flush=True)
    json.dump(out, open(os.path.join(HERE, "heavy.json"), "w"))
print("done", len(out))
