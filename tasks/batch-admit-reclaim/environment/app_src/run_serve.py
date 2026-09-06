import sys

from eng.rd import parse
from eng.step import Eng


def show(names, row):
    out = [names[row[0]], row[1], str(row[2])]
    if row[1] == "preempt":
        out.append("at")
        out.append(str(row[3]))
    elif row[1] == "admit" or row[1] == "resume":
        out.append("from")
        out.append(str(row[3]))
    return " ".join(out)


def main(argv):
    fh = open(argv[1])
    text = fh.read()
    fh.close()
    job = parse(text)
    rows = []
    Eng(job, rows.append).run()
    names = [r.rid for r in job.reqs]
    for row in rows:
        print(show(names, row))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
