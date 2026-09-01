import sys

from pol.drv import Drv
from pol.jrn import parse


def show(row):
    out = []
    for x in row:
        if isinstance(x, list):
            if x and isinstance(x[0], list):
                out.append("[" + " ".join(",".join(str(v) for v in r) for r in x) + "]")
            else:
                out.append("[" + " ".join(str(v) for v in x) + "]")
        else:
            out.append(str(x))
    return " ".join(out)


def main(argv):
    if len(argv) < 2:
        sys.stderr.write("usage: run_hist.py <history-file>\n")
        return 2
    with open(argv[1]) as fh:
        ops = parse(fh.read())
    rows = []
    Drv(ops, rows.append).go()
    for r in rows:
        print(show(r))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
