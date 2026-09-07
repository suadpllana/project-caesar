import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sheet import core


def main(argv):
    p = argv[1]
    nm = os.path.basename(p)
    if nm.endswith(".txt"):
        nm = nm[:-4]
    with open(p) as fh:
        body = fh.read()
    core.drive(body.split("\n"), lambda s: sys.stdout.write("%s %s\n" % (nm, s)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
