import sys

from hold import book

import ops


def main():
    h = book.Hold()
    with open(sys.argv[1], encoding="utf-8") as fh:
        for line in fh:
            f = line.split()
            if f:
                ops.ex(h, tuple(f))
    sys.stdout.write("".join(s + "\n" for s in h.out))


if __name__ == "__main__":
    main()
