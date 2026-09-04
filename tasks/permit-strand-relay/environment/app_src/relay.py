import json
import sys

from lnk.mach import Mach
from lnk.rd import parse


def main():
    rows = []
    with open(sys.argv[1]) as fh:
        plan = parse(fh.read())
    bk = Mach(plan, rows.append).run()
    for row in rows:
        print(json.dumps(list(row)))
    for fd in bk.open():
        print(json.dumps(["park", fd, bk.held(fd)]))


if __name__ == "__main__":
    main()
