import sys

from train import box, ops


def main(a):
    if len(a) != 2:
        sys.stderr.write("usage: run_train.py <run>\n")
        return 2
    run = box.Run()
    out = []
    for op in box.read(a[1]):
        ops.ex(run, op, out)
    for ln in out:
        print(ln)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
