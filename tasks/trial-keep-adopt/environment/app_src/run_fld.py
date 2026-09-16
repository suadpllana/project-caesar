import sys

import ops
from fld import prog, store


def main():
    f = store.Fld()
    for w in prog.read(sys.argv[1]):
        ops.ex(f, w)
    if f.out:
        sys.stdout.write("\n".join(f.out) + "\n")


if __name__ == "__main__":
    main()
