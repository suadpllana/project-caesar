import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sked import emit, lane, read


def main():
    plan = read.load(sys.argv[1])
    for ln in emit.lines(lane.run(plan)):
        print(ln)


main()
