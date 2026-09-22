"""Semantics-only bench: play sessions in-process against the frozen machine, no target process.

    python fastbench.py VARIANT SESSIONS.json OUT.json

A stand-in link calls the machine directly, so a session costs microseconds instead of a
process spawn and round trips. Timing measurements use bench.py, never this.
"""
import json
import os
import sys

import bench

RUNNER = r'''
import json, sys
app, sp, op = sys.argv[1:4]
sys.path.insert(0, app)
from dbg.image import Image
from dbg.sess import play
from tgt.mach import Mach, load_code

class StandIn:
    def __init__(self, text, tape):
        code, entry = load_code(text)
        self.m = Mach(code, entry, tape)
    def pc(self):
        return None if self.m.done else self.m.pc
    def stack(self):
        return None if self.m.done else self.m.rets()
    def step(self):
        return self.m.one()
    def go(self, stops):
        return self.m.go(set(stops))

out = []
for s in json.load(open(sp)):
    img = Image(s["image"])
    lines = []
    err = None
    try:
        play(img, StandIn(s["image"], s["tape"]), s["cmds"], lines.append)
    except Exception as e:
        err = repr(e)[:200]
    out.append({"got": lines, "err": err})
json.dump(out, open(op, "w"))
'''


def run(variant, sessions):
    import shutil
    import subprocess
    import tempfile
    root, app = bench.assemble(variant)
    sp = os.path.join(root, "s.json")
    op = os.path.join(root, "o.json")
    rp = os.path.join(root, "r.py")
    json.dump(sessions, open(sp, "w"))
    open(rp, "w").write(RUNNER)
    subprocess.run([sys.executable, rp, app, sp, op], check=True)
    res = json.load(open(op))
    shutil.rmtree(root)
    return res


if __name__ == "__main__":
    res = run(sys.argv[1], json.load(open(sys.argv[2])))
    json.dump(res, open(sys.argv[3], "w"))
