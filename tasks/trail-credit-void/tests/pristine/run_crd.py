import sys

from crd import ep, say, spec, store, tally


def run(text):
    cfg, seeds, eps = spec.parse(text)
    out = say.Out()
    keep = store.Store()
    for key, value in seeds:
        keep.seed(key, value)
    sums = tally.Sum()
    for one in eps:
        ep.run(cfg, one, keep, sums, out)
    tally.close(sums, out)
    return out.lines


def main(argv):
    if len(argv) != 2:
        sys.stderr.write("usage: run_crd.py <trail-file>\n")
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
