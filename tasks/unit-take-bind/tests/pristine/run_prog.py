import sys

from prog.deck import at
from prog.read import load
from res.tell import line
from res.turn import run


def main(path):
    with open(path, encoding="utf-8") as fh:
        prog = load(fh.read())
    deck = run(prog)
    for un, x in prog.asks:
        print(line(un, x, at(deck, un, x)))


if __name__ == "__main__":
    main(sys.argv[1])
