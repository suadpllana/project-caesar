import sys

from pg import emit, step, store, text


def run(body):
    cap, floor, ops = text.parse(body)
    tr = store.Tree(cap, floor)
    out = emit.Out()
    for kind, key in ops:
        step.one(tr, kind, key, out)
    return out.lines


def main(argv):
    if len(argv) != 2:
        sys.stderr.write("usage: run_idx.py <program>\n")
        return 2
    with open(argv[1], encoding="utf-8") as fh:
        body = fh.read()
    try:
        lines = run(body)
    except text.Bad as exc:
        sys.stderr.write("%s\n" % exc)
        return 1
    for line in lines:
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
