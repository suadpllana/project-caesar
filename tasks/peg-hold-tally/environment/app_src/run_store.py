import sys

from store import ops
from store.host import Host


def main():
    h = Host()
    acc = []
    with open(sys.argv[1], encoding="utf-8") as fh:
        for line in fh:
            bits = line.split()
            if bits:
                ops.ex(h, tuple(bits), acc)
    sys.stdout.write("".join(s + "\n" for s in acc))


main()
