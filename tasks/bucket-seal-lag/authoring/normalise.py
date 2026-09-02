"""LF on every shipped text file, and clear the scratch package.py would ship.

Path.write_text on Windows opens in text mode and turns every newline into CRLF.
A CRLF file inside tests/pristine is copied into the verifier image and executed
there, and a CRLF instruction fails the structural check on a suffix comparison
that no local checker sees, so this runs before packaging every time.
"""

import pathlib
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
TEXT = (".py", ".sh", ".md", ".txt", ".toml", ".json", "Dockerfile", ".dockerignore")


def wanted(p):
    if p.name in ("Dockerfile", ".dockerignore"):
        return True
    return p.suffix in TEXT


def main():
    for d in ROOT.rglob("__pycache__"):
        shutil.rmtree(d, ignore_errors=True)
    for p in sorted(ROOT.rglob("*.pyc")):
        p.unlink()
    fixed = 0
    for p in sorted(ROOT.rglob("*")):
        if not p.is_file() or not wanted(p):
            continue
        raw = p.read_bytes()
        if b"\r\n" in raw:
            p.write_bytes(raw.replace(b"\r\n", b"\n"))
            fixed += 1
            print("LF", p.relative_to(ROOT))
    print("normalised %d files" % fixed)
    return 0


if __name__ == "__main__":
    sys.exit(main())
