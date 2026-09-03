"""LF on every shipped text file, and clear the scratch package.py would ship.

Path.write_text on Windows opens in text mode and turns every newline into a
carriage-return pair, which is how a bundle reaches the structural check with a
ground truth full of CRLF and an instruction whose closing sentence no exact
comparison can match. Nothing here writes CRLF today; this exists so that a
session on another host cannot ship one either.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.dirname(HERE)
TEXT = (".py", ".sh", ".md", ".toml", ".json", ".txt", ".dockerignore", "")
SKIP = ("__pycache__", ".git")


def main():
    fixed, swept = [], []
    for here, dirs, files in os.walk(TASK):
        dirs[:] = [d for d in sorted(dirs) if d not in SKIP]
        if os.path.basename(here) == "__pycache__":
            continue
        for name in sorted(files):
            path = os.path.join(here, name)
            if name.endswith(".pyc"):
                os.remove(path)
                swept.append(os.path.relpath(path, TASK))
                continue
            if os.path.splitext(name)[1] not in TEXT and name != "Dockerfile":
                continue
            with open(path, "rb") as fh:
                raw = fh.read()
            if b"\r\n" in raw:
                with open(path, "wb") as fh:
                    fh.write(raw.replace(b"\r\n", b"\n"))
                fixed.append(os.path.relpath(path, TASK))
    print("normalised %d files, swept %d bytecode files" % (len(fixed), len(swept)))
    for name in fixed:
        print("  LF:", name)
    return 0


if __name__ == "__main__":
    sys.exit(main())
