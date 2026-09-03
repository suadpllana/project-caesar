"""LF on every shipped text file, and clear the scratch a package would otherwise carry.

Windows text writers turn every newline into a carriage return and a newline, and a bundle
that ships CRLF inside tests/pristine executes those files in the verifier. A CRLF
instruction has also failed a structural check here before, on a final sentence that
carried a trailing carriage return no string comparison could match.

    python3 authoring/normalise.py
"""

import pathlib
import shutil
import sys

TASK = pathlib.Path(__file__).resolve().parent.parent
SUFFIX = {".py", ".sh", ".md", ".txt", ".toml", ".json", ""}
SKIP = {"__pycache__", ".git", ".pytest_cache"}


def shipped():
    for p in sorted(TASK.rglob("*")):
        if not p.is_file():
            continue
        if any(part in SKIP for part in p.parts):
            continue
        if p.suffix in SUFFIX:
            yield p


def main():
    fixed = 0
    for p in shipped():
        raw = p.read_bytes()
        if b"\r\n" in raw:
            p.write_bytes(raw.replace(b"\r\n", b"\n"))
            fixed += 1
    gone = 0
    for d in sorted(TASK.rglob("__pycache__")):
        if d.is_dir():
            shutil.rmtree(d, ignore_errors=True)
            gone += 1
    print("normalised %d file(s) to LF, removed %d bytecode director%s"
          % (fixed, gone, "y" if gone == 1 else "ies"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
