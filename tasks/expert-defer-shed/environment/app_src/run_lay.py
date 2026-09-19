import sys

from lay import put, say, spec


def run(text):
    cfg, steps = spec.parse(text)
    out = say.Out()
    for mbs in steps:
        put.step(cfg, mbs, out)
    return out.lines


def main(argv):
    if len(argv) != 2:
        sys.stderr.write("usage: run_lay.py <step-file>\n")
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
