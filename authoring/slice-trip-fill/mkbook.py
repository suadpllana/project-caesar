"""Build the shipped sample of the book-heavy sessions, at about a third of graded scale."""
import random
import sys


def build(seed):
    rng = random.Random(seed)
    mark = 1000
    lines = ["cap 40", "mark %d" % mark]
    oid = 0
    live = []
    for i in range(3000):
        oid += 1
        side = "s" if i % 2 else "b"
        off = 3 + (i % 180)
        px = mark + off if side == "s" else mark - off
        lines.append("new %d %d %s %d %d %s day -"
                     % (oid, 1 + (i % 6), side, px, rng.choice([10, 20, 30, 60]),
                        rng.choice(["-", "-", "4", "7"])))
        live.append(oid)
    for i in range(560):
        oid += 1
        side = "s" if i % 2 else "b"
        px = mark + (2 if side == "s" else -2)
        lines.append("new %d %d %s %d %d - day -"
                     % (oid, 1 + (i % 6), side, px, rng.choice([40, 80])))
        oid += 1
        lines.append("new %d %d %s %d %d %s whole -"
                     % (oid, 1 + (i % 6), "b" if side == "s" else "s", px,
                        rng.choice([20, 40, 90, 160]), rng.choice(["-", "-", "5"])))
        if i % 40 == 11:
            lines.append("pull %d" % rng.choice(live))
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    text = build("shipped-book")
    with open(sys.argv[1], "w", newline="\n") as fh:
        fh.write(text)
    print("%d lines" % text.count("\n"))
