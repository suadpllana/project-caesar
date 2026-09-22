import sys

from lk import name, say, step


def run(text):
    out, book, due, ages = step.run(text)
    for t in sorted(ages, key=lambda x: ages[x]):
        for res in sorted(book.held(t), key=name.key):
            out.append(say.own(t, res, book.eff(t, res)))
        for res in sorted(due.held(t), key=name.key):
            out.append(say.due(t, res, due.owed(t, res)))
    return out


def main():
    with open(sys.argv[1], "r", encoding="utf-8") as fh:
        for line in run(fh.read()):
            print(line)


if __name__ == "__main__":
    main()
