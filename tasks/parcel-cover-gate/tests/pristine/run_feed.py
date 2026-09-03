import sys

from base import drv


def line(row):
    if row[0] == "rd":
        return "%d rd %s %s %s" % (row[1], row[2], row[3], row[4])
    return "%d sh %s %s" % (row[1], row[2],
                            " ".join("%s=%s" % kv for kv in row[3]))


def main(argv):
    if len(argv) < 2:
        sys.stderr.write("usage: run_feed.py <feed>\n")
        return 2
    with open(argv[1]) as fh:
        text = fh.read()
    rows = []
    st = drv.run(text, rows.append)
    for row in rows:
        sys.stdout.write(line(row) + "\n")
    for w, pairs in drv.tail(st):
        sys.stdout.write("end %s %s\n"
                         % (w, " ".join("%s=%s" % kv for kv in pairs)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
