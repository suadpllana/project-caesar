import sys

from reg import book, run


def main(argv):
    if len(argv) < 2:
        sys.stderr.write("usage: screen_reg.py FILE [FILE ...]\n")
        return 2
    for path in argv[1:]:
        with open(path, encoding="utf-8") as fh:
            bk = book.load(fh.read())
        print(path)
        for cid, on, got, seats, board in run.drive(bk):
            print("  %-6s %s %2d/%-2d %s" % (cid, "yes" if on else "no ", got, seats,
                                             " ".join(board)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
