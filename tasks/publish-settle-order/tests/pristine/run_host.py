import sys

import ops
from reg import tab, text


def main(a):
    if len(a) != 2:
        sys.stderr.write("usage: run_host.py <prog>\n")
        return 2
    h = tab.Host()
    out = []
    for op in text.ops(a[1]):
        ops.ex(h, op, out)
    for ln in out:
        print(ln)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
