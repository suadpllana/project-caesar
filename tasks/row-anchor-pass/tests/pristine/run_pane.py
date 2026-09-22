import sys

from pane import frame, say, spec, src


def run(text):
    cfg, decls, evs = spec.parse(text)
    doc = src.Doc(decls)
    out = say.Out()
    frame.play(cfg, doc, evs, out)
    return out.lines


def main(argv):
    if len(argv) != 2:
        sys.stderr.write("usage: run_pane.py <event-file>\n")
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
