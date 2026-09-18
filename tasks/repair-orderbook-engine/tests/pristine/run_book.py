import sys

from mkt.drv import drive
from mkt.rd import read


def main(argv):
    with open(argv[1]) as fh:
        cap, mark, msgs = read(fh.read())
    rows = []
    drive(cap, mark, msgs, rows.append)
    for r in rows:
        print(" ".join(str(c) for c in r))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
