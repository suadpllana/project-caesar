import sys

from rig import hold, lead, ops


def main():
    run = hold.Run()
    with open(sys.argv[1], encoding="utf-8") as fh:
        for line in fh:
            tok = tuple(line.split())
            if tok:
                ops.ex(run, tok)
    lead.close(run)
    for line in run.out:
        sys.stdout.write(line + "\n")


if __name__ == "__main__":
    main()
