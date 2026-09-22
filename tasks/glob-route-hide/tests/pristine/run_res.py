import sys

from fe import fix, rd, say


def run(text):
    prog = rd.load(text)
    tab = fix.settle(prog)
    return [say.line(prog, tab, i) for i in range(len(prog.refs))]


def main():
    if len(sys.argv) != 2:
        sys.exit("usage: run_res.py <program>")
    with open(sys.argv[1], encoding="utf-8") as fh:
        text = fh.read()
    sys.stdout.write("".join(ln + "\n" for ln in run(text)))


if __name__ == "__main__":
    main()
