import sys

from house import bk
from house import ev
from house import rnd


def main(path):
    text = open(path).read()
    who, run, rows = ev.read(text)
    out = []
    b = bk.Book(who, lambda *a: out.append(a))
    for t in range(1, run + 1):
        ev.feed(b, rows, t)
        rnd.turn(b, t)
    for r in out:
        print(" ".join(str(x) for x in r))
    print("--")
    for i, (s, t) in b.sheet().items():
        print(i, s, t)


if __name__ == "__main__":
    main(sys.argv[1])
