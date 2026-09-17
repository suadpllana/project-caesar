import sys

import ops
from hb import store


def main():
    st = store.Store()
    with open(sys.argv[1], encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                ops.ex(st, tuple(line.split()))
    if st.out:
        sys.stdout.write("\n".join(st.out) + "\n")


if __name__ == "__main__":
    main()
