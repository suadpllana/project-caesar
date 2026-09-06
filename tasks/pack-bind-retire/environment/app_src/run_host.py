import os
import sys

from hst import ev


def main(av):
    rows = []
    for p in av:
        ev.go(os.path.basename(p)[:-4], p, rows)
    for r in rows:
        print(r)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
