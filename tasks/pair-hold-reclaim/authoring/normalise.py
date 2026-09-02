"""LF on every shipped text file, and clear the scratch package.py would otherwise ship.

The tree passing every gate says nothing about the archive. A CRLF file inside
tests/pristine is worse than one in the instruction, because those files are copied into
the verifier image and executed.

    python3 authoring/normalise.py
"""

import pathlib
import shutil
import sys

TASK = pathlib.Path(__file__).resolve().parent.parent
TEXT = (".py", ".sh", ".txt", ".md", ".toml", ".json", ".dockerignore")
SKIP = ("__pycache__", ".git")


def main():
    fixed = 0
    for p in sorted(TASK.rglob("*")):
        if any(s in p.parts for s in SKIP):
            continue
        if p.is_dir():
            if p.name == "__pycache__":
                shutil.rmtree(p, ignore_errors=True)
            continue
        if p.suffix not in TEXT and p.name != "Dockerfile" and p.name != ".dockerignore":
            continue
        raw = p.read_bytes()
        if b"\r\n" in raw:
            p.write_bytes(raw.replace(b"\r\n", b"\n"))
            fixed += 1
            print("normalised %s" % p.relative_to(TASK))
    for d in sorted(TASK.rglob("__pycache__")):
        shutil.rmtree(d, ignore_errors=True)
    for p in sorted((TASK / "tests").glob("nonce")):
        p.unlink()
    print("%d file(s) had CRLF; scratch cleared" % fixed)
    return 0


if __name__ == "__main__":
    sys.exit(main())
