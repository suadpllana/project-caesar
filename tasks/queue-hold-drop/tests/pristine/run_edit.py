import sys

from pend import scan, step, store


def main(argv):
    st = store.St()
    with open(argv[1], encoding="utf-8") as fh:
        text = fh.read()
    for op in scan.ops(text):
        step.run(st, op)
    sys.stdout.write("".join(line + "\n" for line in st.out))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
