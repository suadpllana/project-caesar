import sys

import ops
import plan


def main():
    box = plan.Box()
    with open(sys.argv[1], encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                ops.ex(box, tuple(line.split()))
    if box.out:
        sys.stdout.write("\n".join(box.out) + "\n")


if __name__ == "__main__":
    main()
