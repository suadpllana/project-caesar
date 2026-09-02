import json
import sys

from flow.gr import parse
from flow.mach import Mach


def main(argv):
    with open(argv[1]) as fh:
        text = fh.read()
    rows = []
    Mach(parse(text), rows.append).run()
    for r in rows:
        sys.stdout.write(json.dumps(r, separators=(", ", ": ")) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
