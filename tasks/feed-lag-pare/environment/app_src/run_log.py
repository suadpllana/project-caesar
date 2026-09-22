import sys

from lg import fold, pare, pin, read, say, store, tell


def run(text):
    out = say.Say()
    st = store.Store()
    pn = pin.Pins(st)
    for cmd in read.parse(text):
        op = cmd[0]
        if op in ("set", "add", "del"):
            st.append(op, cmd[1], cmd[2])
        elif op == "mark":
            pn.mark(cmd[1])
        elif op == "unmark":
            pn.unmark(cmd[1])
        elif op == "feed":
            pn.feed(cmd[1], cmd[2], cmd[3])
        elif op == "ack":
            pn.ack(cmd[1], cmd[2])
        elif op == "close":
            pn.close(cmd[1])
        elif op == "read":
            val = fold.value(st, cmd[2], pn.point_of(cmd[1]))
            out.line("val %s %d %s" % (cmd[1], cmd[2], tell.shown(val)))
        elif op == "pare":
            gone = pare.run(st, pn, cmd[1])
            out.line("pare %d %d" % (gone, st.count()))
    for line in tell.report(st):
        out.line(line)
    return out.lines


def main():
    with open(sys.argv[1], "r", encoding="utf-8") as fh:
        text = fh.read()
    for line in run(text):
        print(line)


if __name__ == "__main__":
    main()
