import sys

from st import vol
import ops


def main():
    st = vol.Store()
    with open(sys.argv[1], encoding="utf-8") as fh:
        for line in fh:
            a = tuple(line.split())
            if a:
                ops.ex(st, a)
    sys.stdout.write("".join(x + "\n" for x in st.out))


if __name__ == "__main__":
    main()
