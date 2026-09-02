"""LF on every shipped text file, and clear the scratch package.py would otherwise ship.

Path.write_text on a Windows host opens in text mode and turns every newline into a pair, so
a generator run there re-dirties whatever was normalised by hand. This is the pass that puts
it back, and it is cheap enough to run before every package.
"""
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEXT = {".py", ".sh", ".md", ".json", ".txt", ".toml", ""}
SKIP = {"__pycache__", ".pytest_cache"}


def main():
    fixed = 0
    for p in sorted(ROOT.rglob("*")):
        if not p.is_file() or any(s in p.parts for s in SKIP):
            continue
        if p.suffix.lower() not in TEXT and p.name != "Dockerfile" and p.name != ".dockerignore":
            continue
        raw = p.read_bytes()
        if b"\r\n" in raw:
            p.write_bytes(raw.replace(b"\r\n", b"\n"))
            fixed += 1
    for d in sorted(ROOT.rglob("__pycache__")):
        shutil.rmtree(d, ignore_errors=True)
    for d in sorted(ROOT.rglob(".pytest_cache")):
        shutil.rmtree(d, ignore_errors=True)
    print("normalised %d files, scratch cleared" % fixed)


if __name__ == "__main__":
    main()
