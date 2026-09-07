"""Build the shipped sample of the large sessions, at about a third of the graded scale."""
import random
import sys

sys.path.insert(0, ".")
import gen


def build(seed):
    rng = random.Random(seed)
    mark = 1000
    lines = ["cap 40", "mark %d" % mark]
    oid = 0
    for i in range(56):
        oid += 1
        side = "s" if i % 2 else "b"
        off = 1 + (i % 9)
        px = mark + off if side == "s" else mark - off
        lines.append("new %d %d %s %d %d %s day -"
                     % (oid, 1 + (i % 5), side, px, rng.choice([20, 40, 60]),
                        rng.choice(["-", "5", "8"])))
    live = list(range(1, oid + 1))
    for i in range(4200):
        oid += 1
        side = "b" if i % 2 else "s"
        trp = mark + (60 + (i % 400)) * (1 if side == "b" else -1)
        lines.append("new %d %d %s %d %d - day %d"
                     % (oid, 1 + (i % 5), side, mark, 10, trp))
        live.append(oid)
    for i in range(18):
        oid += 1
        side = "s" if i % 2 else "b"
        px = mark + (1 if side == "s" else -1)
        qty = rng.randrange(15000, 20000, 100)
        lines.append("new %d 9 %s %d %d %d day -"
                     % (oid, side, px, qty, rng.choice([2, 3, 4])))
        oid += 1
        lines.append("new %d 8 %s %d %d - part -"
                     % (oid, "b" if side == "s" else "s", px, qty))
        if i % 9 == 4:
            oid += 1
            lines.append("new %d 7 %s %d %d - whole -"
                         % (oid, "b" if side == "s" else "s", px,
                            rng.choice([10, 40, 90])))
        if i % 13 == 6:
            lines.append("pull %d" % rng.choice(live))
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    text = build("shipped-wide")
    with open(sys.argv[1], "w", newline="\n") as fh:
        fh.write(text)
    print("%d lines" % text.count("\n"))
