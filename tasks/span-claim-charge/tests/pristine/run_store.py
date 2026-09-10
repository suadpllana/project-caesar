import sys

from base import feed


def main():
    with open(sys.argv[1], encoding="utf-8") as fh:
        raw = fh.read().splitlines()
    for row in feed.run(raw):
        print(row)


if __name__ == "__main__":
    main()
