import json
import sys

from note.board import Board
from rev.store import Store


def load(path):
    opens = []
    store = Store()
    with open(path) as fh:
        for raw in fh:
            row = raw.rstrip("\n")
            if not row or row.startswith("#"):
                continue
            head, _, rest = row.partition(" ")
            if head == "rev":
                store.land(rest.split("|") if rest else [])
            elif head == "note":
                bits = rest.split()
                opens.append((store.head(), int(bits[0]), int(bits[1])))
    return store, opens


def main():
    store, opens = load(sys.argv[1])
    live, log = Board(store).build(opens)
    for note in sorted(live, key=lambda n: n["id"]):
        print("note %d %d" % (note["id"], note["line"]))
    for entry in log:
        print(" ".join(str(x) for x in entry))


if __name__ == "__main__":
    main()
