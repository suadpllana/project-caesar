import sys

import ops
from mix import hold


def main():
    h = hold.Hold()
    with open(sys.argv[1], encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                ops.ex(h, tuple(line.split()))
    for line in h.out:
        sys.stdout.write(line + "\n")


if __name__ == "__main__":
    main()
