"""Time one draw of the long family at a chosen group count.

    python3 -u time_long.py <pane|model> <groups> [seed]
"""
import inspect
import random
import sys
import time

import lab

cases, gen, model = lab.sealed()


def build(ng, seed):
    text = inspect.getsource(gen.long).replace("ng = 500000", "ng = %d" % ng)
    assert "ng = %d" % ng in text
    ns = {}
    exec(compile(text, "long", "exec"), gen.__dict__, ns)
    return ns["long"](random.Random(seed))


def main(argv):
    which, ng = argv[1], int(argv[2])
    seed = argv[3] if len(argv) > 3 else "tl"
    doc = build(ng, seed)
    run = model.expect if which == "model" else lab.pane(which)
    t = time.time()
    out = run(doc)
    print("%s ng=%d %.1fs %s" % (which, ng, time.time() - t, out[-1]), flush=True)


if __name__ == "__main__":
    main(sys.argv)
