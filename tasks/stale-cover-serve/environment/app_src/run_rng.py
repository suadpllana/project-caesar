import sys

from rng import ask, out, seg, spec, store


def run(text):
    prog = spec.parse(text)
    st = store.Store(prog.span)
    tb = seg.Table()
    lines = []
    staged = []
    for op in prog.ops:
        tag = op[0]
        if tag == "w":
            staged.append((op[1], op[2]))
        elif tag == "x":
            staged.append((op[1], None))
        elif tag == "c":
            now, touched = st.commit(staged)
            staged = []
            ask.settle(tb, touched, now, prog.tune)
            lines.append(out.ver(now))
        else:
            lines.extend(ask.read(tb, st, op[1], op[2], op[3], prog.tune))
    return lines


def main():
    with open(sys.argv[1], "r", encoding="utf-8") as fh:
        text = fh.read()
    for line in run(text):
        print(line)


if __name__ == "__main__":
    main()
