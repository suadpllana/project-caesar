"""LF on every shipped text file, and clear the scratch package.py would otherwise ship.

Path.write_text on a Windows host translates every newline, so a generator run there
leaves CRLF inside the bundle. CRLF in the instruction fails the structural check on a
sentence that is perfectly correct, and CRLF inside tests/pristine is worse, because those
files are copied into the verifier image and executed.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

TASK = Path(__file__).resolve().parent.parent
TEXT = {".py", ".sh", ".md", ".txt", ".toml", ".json"}


def main():
    fixed = []
    for path in sorted(TASK.rglob("*")):
        if not path.is_file() or path.suffix not in TEXT:
            continue
        if "__pycache__" in path.parts:
            continue
        raw = path.read_bytes()
        if b"\r\n" in raw:
            path.write_bytes(raw.replace(b"\r\n", b"\n"))
            fixed.append(str(path.relative_to(TASK)))
    for junk in list(TASK.rglob("__pycache__")) + list(TASK.rglob("*.pyc")):
        if junk.is_dir():
            shutil.rmtree(junk, ignore_errors=True)
        elif junk.is_file():
            junk.unlink()
    print("normalised %d file(s) to LF; scratch cleared" % len(fixed))
    for f in fixed:
        print("   %s" % f)
    return 0


if __name__ == "__main__":
    sys.exit(main())
