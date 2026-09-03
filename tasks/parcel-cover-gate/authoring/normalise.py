"""LF on every shipped text file, and clear the scratch package.py would ship.

The tree passing every gate says nothing about the archive. A CRLF pair inside
`tests/pristine` is worse than one in the brief, because those files are copied
into the verifier image and executed there, and a Python text writer on some
hosts turns every newline into a pair without anybody asking it to. So this runs
before packaging, every time, and `tools/zipcheck.py` runs after it on the zip.

It also clears `__pycache__` and `*.pyc` out of the bundle. `package.py` is
faithful to the tree, which means it will happily ship bytecode compiled by the
authoring host into an image built for a different one.
"""

import pathlib
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
TEXT = {".py", ".sh", ".md", ".toml", ".json", ".txt", ""}
SKIP = {"__pycache__", ".git"}


def main():
    fixed, swept = [], []
    for path in sorted(ROOT.rglob("*")):
        if any(part in SKIP for part in path.parts):
            if path.is_dir() and path.name == "__pycache__":
                shutil.rmtree(path, ignore_errors=True)
                swept.append(path.relative_to(ROOT).as_posix())
            continue
        if path.is_file() and path.suffix == ".pyc":
            path.unlink()
            swept.append(path.relative_to(ROOT).as_posix())
            continue
        if not path.is_file() or path.suffix not in TEXT:
            continue
        raw = path.read_bytes()
        if b"\r\n" in raw:
            path.write_bytes(raw.replace(b"\r\n", b"\n"))
            fixed.append(path.relative_to(ROOT).as_posix())
    print("%d files normalised to LF, %d scratch paths cleared"
          % (len(fixed), len(swept)))
    for rel in fixed:
        print("  LF  " + rel)
    for rel in swept[:10]:
        print("  rm  " + rel)
    return 0


if __name__ == "__main__":
    sys.exit(main())
