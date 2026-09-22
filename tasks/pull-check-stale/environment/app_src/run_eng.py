import sys

from eng import plan
from eng.say import Say
from eng.keep import Keep
from eng.hold import Board
from eng.wake import Wake


def run(p):
    out = Say()
    keep = Keep()
    board = Board(p)
    wake = Wake(p, keep, board, out)
    for path, word in p.seeds:
        keep.put(path, word)
    for n, rd in enumerate(p.rounds, 1):
        out.round(n)
        wake.open_round()
        for d in rd:
            if d[0] == "put":
                keep.put(d[1], d[2])
            elif d[0] == "cut":
                keep.cut(d[1])
            else:
                wake.request(d[1])
    return out.text()


def build(path):
    return run(plan.read_plan(path))


def main(argv):
    if len(argv) != 2:
        sys.stderr.write("usage: run_eng.py <program>\n")
        return 2
    sys.stdout.write(build(argv[1]) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
