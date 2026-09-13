import sys

from pan import ask, edit, grid, say, seat, step


def main():
    p = grid.new()
    with open(sys.argv[1], encoding="utf-8") as fh:
        for line in fh:
            t = tuple(line.split())
            if not t:
                continue
            o = t[0]
            if o == "bulk":
                edit.bulk(p, int(t[1]), int(t[2]), int(t[3]))
            elif o == "ins":
                edit.ins(p, int(t[1]), t[2], int(t[3]))
            elif o == "del":
                edit.dele(p, t[1])
            elif o == "move":
                edit.move(p, t[1], int(t[2]))
            elif o == "set":
                edit.rest(p, t[1], int(t[2]))
            elif o == "span":
                edit.span(p, int(t[1]))
            elif o == "roll":
                seat.roll(p, int(t[1]))
            elif o == "pass":
                step.pas(p)
            elif o == "top":
                ask.top(p)
            elif o == "tall":
                ask.tall(p)
            elif o == "face":
                ask.face(p)
            else:
                raise SystemExit("bad op %s" % o)
    out = say.drain()
    if out:
        sys.stdout.write("\n".join(out) + "\n")


if __name__ == "__main__":
    main()
