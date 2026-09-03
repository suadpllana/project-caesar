import sys

from pnl.lex import parse
from pnl.loop import Loop


def main(argv):
    if len(argv) < 2:
        sys.stderr.write("usage: run_panel.py <panel.txt>\n")
        return 2
    for path in argv[1:]:
        with open(path) as fh:
            feeds, gauges, latch, rounds, order = parse(fh.read())
        rows = []
        lp = Loop(feeds, gauges, latch, rounds, order, rows.append)
        try:
            dump = lp.go()
        except Exception as exc:
            print("%s: %s: %s" % (path, type(exc).__name__, exc))
            continue
        print(path)
        for r in rows:
            print("  %d %s %s %d" % r)
        for n, v in dump:
            print("  = %s %d" % (n, v))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
