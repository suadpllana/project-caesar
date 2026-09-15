import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import ops
from kv import store


def main():
    kv = store.Kv()
    with open(sys.argv[1], encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                ops.ex(kv, tuple(line.split()))
    if kv.out:
        sys.stdout.write("\n".join(kv.out) + "\n")


if __name__ == "__main__":
    main()
