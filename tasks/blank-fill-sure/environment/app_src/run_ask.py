import sys

from rs import keep, load, say


def run(text):
    st = load.read(text)
    return say.lines(st, keep.report(st))


def main():
    with open(sys.argv[1], encoding="utf-8") as fh:
        text = fh.read()
    for line in run(text):
        print(line)


if __name__ == "__main__":
    main()
