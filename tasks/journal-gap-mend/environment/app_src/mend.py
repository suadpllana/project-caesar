import sys

from jl import read, seek


def run(text):
    return seek.mend(read.parse(text))


def main(argv):
    if len(argv) != 2:
        sys.stderr.write("usage: mend.py <journal>\n")
        return 2
    with open(argv[1], encoding="utf-8") as fh:
        text = fh.read()
    try:
        lines = run(text)
    except ValueError as exc:
        sys.stderr.write("%s\n" % exc)
        return 1
    for line in lines:
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
