import json
import sys

from bind.mc import Mach
from bind.rd import parse


def main(argv):
    with open(argv[1]) as fh:
        sp = parse(fh.read())
    rows = []
    Mach(sp, rows.append).run()
    for row in rows:
        sys.stdout.write(json.dumps(list(row)) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
