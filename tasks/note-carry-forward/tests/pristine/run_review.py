import sys

from note.board import Board
from rev.store import Store


def load(path):
    events = []
    store = Store()
    with open(path) as fh:
        for raw in fh:
            row = raw.rstrip("\n")
            if not row or row.startswith("#"):
                continue
            head, _, rest = row.partition(" ")
            if head == "rev":
                store.land(rest.split("|") if rest else [])
            elif head == "open":
                bits = rest.split()
                lo, hi = int(bits[1]), int(bits[2])
                events.append((store.head(), "open",
                               (int(bits[0]), list(range(lo, hi + 1)))))
            elif head in ("reply", "resolve"):
                events.append((store.head(), head, int(rest)))
    return store, events


def main():
    store, events = load(sys.argv[1])
    threads, log = Board(store).build(events)
    for thread in sorted(threads, key=lambda t: t["id"]):
        print("thread %d %s %s" % (thread["id"], thread["state"],
                                   ",".join(str(x) for x in sorted(thread["span"])) or "-"))
    for entry in log:
        print(" ".join(str(x) for x in entry))


if __name__ == "__main__":
    main()
