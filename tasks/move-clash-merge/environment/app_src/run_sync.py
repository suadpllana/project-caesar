import sys

from mrg import drive


def main(argv):
    with open(argv[1], encoding="utf-8") as fh:
        lines = fh.read().split("\n")
    drive.go(lines, print)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
