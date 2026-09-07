import sys

from sheet.core import Run


def main(argv):
    with open(argv[1]) as fh:
        lines = fh.read().split("\n")
    rows = []
    Run(rows.append).run(lines)
    for n, verb, at, body in rows:
        sys.stdout.write("%d %s %s | %s\n" % (n, verb, at, body))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
