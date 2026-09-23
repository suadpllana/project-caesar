import sys

from sr.page import Page
from sr.script import Bad, parse
from sr.voice import Reader


def run(text):
    last, ticks = parse(text)
    pg = Page()
    for op in ticks[0]:
        pg.apply(op)
    rd = Reader(pg)
    rd.load()
    out = []
    for t in range(1, last + 1):
        recs = [pg.apply(op) for op in ticks.get(t, ())]
        out.extend(rd.step(t, recs))
    return out


def main(argv):
    if len(argv) != 2:
        sys.stderr.write("usage: run_sr.py <page-script>\n")
        return 2
    with open(argv[1], encoding="utf-8") as fh:
        text = fh.read()
    try:
        lines = run(text)
    except Bad as exc:
        sys.stderr.write("%s\n" % exc)
        return 1
    for line in lines:
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
