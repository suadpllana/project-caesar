import sys

from pipe import read, say, win


def main(argv):
    if len(argv) != 2:
        sys.stderr.write("usage: run_shard.py <shard>\n")
        return 2
    rack = win.Rack(say.Sink())
    for op in read.ops(argv[1]):
        k = op[0]
        if k == "rec":
            rack.rec(op[1], op[2], op[3])
        elif k == "width":
            rack.wid(op[1])
        elif k == "span":
            rack.spn(op[1])
        elif k == "floor":
            rack.flr(op[1])
        else:
            rack.seal()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
