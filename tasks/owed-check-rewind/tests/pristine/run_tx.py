#!/usr/bin/env python3
import sys

from tx import prog, say, sess


def run(text):
    p = prog.load(text)
    s = sess.Session(p.cat, p.rows)
    return [say.line(s.step(st)) for st in p.stmts]


def main():
    with open(sys.argv[1], encoding="utf-8") as fh:
        text = fh.read()
    for out in run(text):
        print(out)


if __name__ == "__main__":
    main()
