import sys

import ops
from st import tree


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
        sys.stderr.write("usage: run_store.py <script>\n")
        return 2
    for ln in ops.run(tree.St(), read(a[1])):
        print(ln)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
