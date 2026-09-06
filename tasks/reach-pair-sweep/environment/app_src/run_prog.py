import sys

from rt import ex, hp, rd


def main(a):
    if len(a) != 2:
        sys.stderr.write("usage: run_prog.py <prog>\n")
        return 2
    h = hp.Hp()
    out = []
    for op in rd.rd(a[1]):
        ex.ex(h, op, out)
    for ln in out:
        print(ln)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
