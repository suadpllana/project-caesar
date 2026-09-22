import sys

from led import spec
from led import step
from led import ver


def run(text):
    out = []
    store = ver.Store()
    box = {}
    for op in spec.read(text):
        step.one(store, box, op, out)
    return out


def main():
    with open(sys.argv[1]) as fh:
        text = fh.read()
    for line in run(text):
        print(line)


if __name__ == "__main__":
    main()
