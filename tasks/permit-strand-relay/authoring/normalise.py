"""LF on every shipped text file, and clear the scratch package.py would ship."""

import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TEXT = (".py", ".sh", ".md", ".json", ".txt", ".toml", "Dockerfile", ".dockerignore")


def main():
    swept = 0
    for here, dirs, leaves in os.walk(ROOT):
        for junk in [d for d in dirs if d == "__pycache__"]:
            shutil.rmtree(os.path.join(here, junk), ignore_errors=True)
            dirs.remove(junk)
            swept += 1
        for leaf in sorted(leaves):
            if leaf.endswith(".pyc"):
                os.remove(os.path.join(here, leaf))
                swept += 1
    fixed = 0
    for here, _, leaves in os.walk(ROOT):
        for leaf in sorted(leaves):
            if not (leaf.endswith(TEXT) or leaf == "Dockerfile"):
                continue
            path = os.path.join(here, leaf)
            with open(path, "rb") as fh:
                body = fh.read()
            if b"\r\n" in body:
                with open(path, "wb") as fh:
                    fh.write(body.replace(b"\r\n", b"\n"))
                fixed += 1
    print("swept %d scratch item(s), normalised %d file(s) to LF" % (swept, fixed))
    return 0


if __name__ == "__main__":
    sys.exit(main())
