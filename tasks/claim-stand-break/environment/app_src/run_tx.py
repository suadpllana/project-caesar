import sys

from tx import path, prog, say


def run(text):
    out = say.Out()
    path.play(prog.parse(text), out)
    return out.lines


def main(argv):
    if len(argv) != 2:
        sys.stderr.write("usage: run_tx.py <program>\n")
        return 2
    with open(argv[1], encoding="utf-8") as fh:
        text = fh.read()
    try:
        lines = run(text)
    except prog.Bad as exc:
        sys.stderr.write("%s\n" % exc)
        return 1
    for line in lines:
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
