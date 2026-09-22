import sys

from bm import spec
from bm import walk


def run(text):
    sp = spec.parse(text)
    out = []
    for name, prompt in sp.asks:
        out.extend(walk.one(sp, name, prompt))
    return out


def main():
    with open(sys.argv[1], "r", encoding="utf-8") as fh:
        text = fh.read()
    for line in run(text):
        print(line)


if __name__ == "__main__":
    main()
