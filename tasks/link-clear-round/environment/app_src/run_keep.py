import sys

from keep import lay, say, spec, store


def run(text):
    tabs, links, ops = spec.parse(text)
    st = store.Store(tabs)
    out = say.Out()
    work = lay.open(st, links)
    for op in ops:
        lay.run(work, op, out)
    return out.lines


def main(argv):
    if len(argv) != 2:
        sys.stderr.write("usage: run_keep.py <program>\n")
        return 2
    with open(argv[1], encoding="utf-8") as fh:
        text = fh.read()
    try:
        lines = run(text)
    except spec.Bad as exc:
        sys.stderr.write("%s\n" % exc)
        return 1
    for line in lines:
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
