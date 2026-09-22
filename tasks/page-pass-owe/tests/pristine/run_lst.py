import sys

from lst import edt
from lst import pg
from lst import rep
from lst import say
from lst import scr
from lst import spec


def run(text):
    prog = spec.load(text)
    st = scr.State(prog.hold)
    out = say.Out()
    for op in prog.ops:
        kind = op[0]
        if kind == "row" or kind == "add":
            edt.add(st, op[1], op[2], op[3], op[4])
        elif kind == "move":
            edt.move(st, op[1], op[2])
        elif kind == "tag":
            edt.retag(st, op[1], op[2])
        elif kind == "drop":
            edt.drop(st, op[1])
        elif kind == "open":
            scr.open_scroll(st, op[1], op[2], op[3], op[4])
        elif kind == "next":
            out.page(op[1], pg.serve(st, op[1]))
    lines, total = rep.close(st)
    out.report(lines, total)
    return out.lines


def main(argv):
    with open(argv[1]) as fh:
        text = fh.read()
    sys.stdout.write("\n".join(run(text)) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
