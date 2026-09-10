import sys

import ops
from reg import live, text


def main():
    span, part, body = text.load(sys.argv[1])
    h = live.Pool(span, part)
    out = []
    for line in body:
        ops.ex(h, tuple(line.split()), out)
    sys.stdout.write("".join(x + "\n" for x in out))


if __name__ == "__main__":
    main()
