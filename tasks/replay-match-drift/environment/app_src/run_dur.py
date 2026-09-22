import sys

from dur import mach


def run(text):
    return mach.run(text)


def main():
    with open(sys.argv[1], "r", encoding="utf-8") as fh:
        text = fh.read()
    for line in run(text):
        print(line)


if __name__ == "__main__":
    main()
