import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import readings


def main(argv):
    for path in argv[1:]:
        with open(path) as fh:
            text = fh.read()
        print("=== %s" % os.path.basename(path))
        for row in readings.run(readings.REFERENCE, text):
            print(" ".join(str(c) for c in row))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
