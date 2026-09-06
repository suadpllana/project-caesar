import os
import sys

from strm import req


def main(av):
    rows = []
    for p in av:
        req.run(os.path.basename(p).split(".")[0], p, rows)
    for r in rows:
        print(r)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
