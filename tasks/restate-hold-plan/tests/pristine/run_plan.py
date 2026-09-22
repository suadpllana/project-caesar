import sys

from plan.order import order
from plan.pipe import Bad, load
from plan.reach import reach
from plan.settle import settle


def run(text):
    pp = load(text)
    return [" ".join(str(word) for word in row) for row in order(pp, settle(pp, reach(pp)))]


def main(argv):
    if len(argv) != 2:
        print("usage: run_plan.py PIPELINE", file=sys.stderr)
        return 2
    with open(argv[1], encoding="utf-8") as fh:
        text = fh.read()
    try:
        lines = run(text)
    except Bad as exc:
        print("run_plan: %s" % exc, file=sys.stderr)
        return 1
    for line in lines:
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
