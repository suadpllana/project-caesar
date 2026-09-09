import pathlib
import sys

import lab

TASK = lab.TASK
which = sys.argv[1] if len(sys.argv) > 1 else "ref"
overlay = None if which == "ship" else TASK / "solution"
lb = lab.Lab(overlay)
for p in sys.argv[2:]:
    print("--", p)
    for ln in lb.run(lab.prog(pathlib.Path(p))):
        print(ln)
lb.close()
