"""Cut a segment file down to its first R rows, keeping headers truthful."""
import sys


def cut(text, R):
    lines = text.split("\n")
    head = lines[0].split()
    g = int(head[1])
    out = ["seg %d %d %s" % (g, R, head[3])]
    pos = {}
    cur = None
    for line in lines[1:]:
        if not line:
            continue
        f = line.split()
        t = f[0]
        if t == "ch":
            c = int(f[1])
            cur = [c, line, []]
            if pos.get(c, 0) < R:
                out.append(line)
        elif t == "pg":
            c = cur[0]
            s = pos.get(c, 0)
            n = int(f[1])
            pos[c] = s + n
            if s >= R:
                continue
            if s + n <= R:
                out.append(line)
                continue
            keep = R - s
            form = f[7]
            toks = f[8:8 + n][:keep]
            if form == "i":
                dic = [int(x) for x in cur[1].split()[4:]]
                vals = [None if x == "-" else dic[int(x)] for x in toks]
            else:
                vals = [None if x == "-" else int(x) for x in toks]
            nn = [x for x in vals if x is not None]
            u = keep - len(nn)
            if not nn:
                out.append("pg %d %d - - %s 0 %s %s" % (keep, u, f[5], form, " ".join(toks)))
                continue
            a, b = min(nn), max(nn)
            if f[5] == "w":
                a, b = -((-a) // g) * g, (b // g) * g
            out.append("pg %d %d %d %d %s %d %s %s" % (keep, u, a, b, f[5], sum(nn), form, " ".join(toks)))
        elif t == "up":
            if int(f[2]) < R:
                out.append(line)
        elif t == "del":
            if int(f[1]) < R:
                out.append(line)
        else:
            out.append(line)
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    src, R, dst = sys.argv[1], int(sys.argv[2]), sys.argv[3]
    with open(src, encoding="utf-8") as fh:
        text = fh.read()
    with open(dst, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(cut(text, R))
