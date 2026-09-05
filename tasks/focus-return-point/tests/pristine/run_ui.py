import sys

from ui.core import Ui


def main(argv):
    with open(argv[1]) as fh:
        lines = fh.read().split("\n")
    rows = []
    ui = Ui(rows.append)
    ui.run(lines)
    for n, ev, fo in rows:
        print("%d %s -> %s" % (n, ev, fo))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
