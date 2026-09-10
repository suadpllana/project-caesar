import sys

import ops
from tab import store


def main():
    tab = store.Tab()
    with open(sys.argv[1], encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                ops.ex(tab, tuple(line.split()))
    out = tab.out
    if out:
        sys.stdout.write("\n".join(out) + "\n")


if __name__ == "__main__":
    main()
