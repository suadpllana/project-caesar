import sys

import ops
from opt import reg


def main():
    r = reg.Reg()
    with open(sys.argv[1], encoding="utf-8") as fh:
        for line in fh:
            t = tuple(line.split())
            if t:
                ops.ex(r, t)
    sys.stdout.write("".join(x + "\n" for x in r.out))


if __name__ == "__main__":
    main()
