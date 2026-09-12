import sys

import ops
from bind import book


def main():
    job = book.Job()
    with open(sys.argv[1], encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                ops.ex(job, tuple(line.split()))
    out = job.out
    if out:
        sys.stdout.write("\n".join(out) + "\n")


if __name__ == "__main__":
    main()
