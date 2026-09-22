import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dbg.image import load
from dbg.sess import play
from tgt.link import spawn


def main():
    if len(sys.argv) != 4:
        sys.exit("usage: run_dbg.py IMAGE SCRIPT TAPE")
    img = load(sys.argv[1])
    link = spawn(sys.argv[1], sys.argv[3])
    with open(sys.argv[2]) as f:
        cmds = f.read().splitlines()
    try:
        play(img, link, cmds, print)
    finally:
        link.close()


if __name__ == "__main__":
    main()
