import sys

from srv import wire


def main():
    if len(sys.argv) != 2:
        print("usage: run_stream.py <job file>")
        return 2
    with open(sys.argv[1], "r") as fh:
        job = wire.load(fh.read())
    for row in wire.drive(job):
        print(" ".join(str(x) for x in row))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
