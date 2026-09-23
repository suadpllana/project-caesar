import sys

from scn import emit, live, parse, pick, proj


def run(text):
    seg, queries = parse.load(text)
    out = emit.Out()
    mem = live.fresh(seg)
    for i, q in enumerate(queries):
        out.qry(i)
        st = live.start(seg, q, mem)
        pick.run(seg, q, st, out)
        rows = live.rows(st)
        out.sel(len(rows), emit.digest(rows))
        proj.run(seg, q, st, rows, out)
    return out.lines


def main():
    with open(sys.argv[1], encoding="utf-8") as fh:
        text = fh.read()
    sys.stdout.write("\n".join(run(text)) + "\n")


if __name__ == "__main__":
    main()
