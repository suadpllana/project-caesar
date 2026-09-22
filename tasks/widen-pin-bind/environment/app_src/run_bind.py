import sys

from res import say, spec, walk


def run(text):
    prog = spec.parse(text)
    state = walk.new(prog)
    out = []
    for k, node in enumerate(prog.asks):
        out.extend(say.lines(k, walk.ask(state, node)))
    out.append(say.tally(walk.total(state)))
    return out


def main():
    with open(sys.argv[1], "r", encoding="utf-8") as fh:
        text = fh.read()
    for line in run(text):
        print(line)


if __name__ == "__main__":
    main()
