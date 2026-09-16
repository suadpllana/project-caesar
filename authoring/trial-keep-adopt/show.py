import sys

import lab

which = sys.argv[1]
here = lab.ref() if which == "ref" else lab.shipped()
with open(sys.argv[2], encoding="utf-8") as fh:
    lines = fh.read().splitlines()
for line in lab.trace(here, lines):
    print(line)
