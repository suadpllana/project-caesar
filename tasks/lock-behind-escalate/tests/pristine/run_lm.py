import sys

from lm import say, sched, spec


def run(text):
    cfg, txns = spec.parse(text)
    out = say.Out()
    sched.run(cfg, txns, out)
    return out.lines


def main(argv):
    if len(argv) != 2:
        sys.stderr.write("usage: run_lm.py <script>\n")
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
