import sys

import ops
from mem import heap


def read(p):
    out = []
    with open(p) as f:
        for ln in f:
            ln = ln.strip()
            if ln:
                out.append(tuple(ln.split()))
    return out


def main(a):
    if len(a) != 2:
        sys.stderr.write("usage: run_prog.py <prog>\n")
        return 2
    h = heap.Heap()
    out = []
    for op in read(a[1]):
        ops.ex(h, op, out)
    for ln in out:
        print(ln)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
