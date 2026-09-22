import sys

from lk import ask, read, tell


def run(text):
    out = []
    eng = ask.Engine(out)
    for cmd in read.parse(text):
        eng.step(cmd)
    out.extend(tell.report(eng))
    return out


def main():
    with open(sys.argv[1], "r", encoding="utf-8") as fh:
        text = fh.read()
    for line in run(text):
        print(line)


if __name__ == "__main__":
    main()
