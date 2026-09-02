import sys

from core import ex, lg, rd
from core import st as store


def main(path):
    log = lg.Log()
    s = store.Store(log.put)
    ex.apply(s, rd.parse(open(path).read()))
    out = log.text()
    if out:
        print(out)
    print("--")
    for line in ex.snap(s):
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
