"""LF on every shipped text file, and clear the scratch package.py would otherwise ship."""
import os
import shutil

import stage

TEXT = (".py", ".sh", ".md", ".txt", ".json", ".toml", "Dockerfile", ".dockerignore")


def main():
    fixed = 0
    for root, dirs, files in os.walk(stage.TASK):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for name in sorted(files):
            path = os.path.join(root, name)
            if not (name.endswith(TEXT) or name in ("Dockerfile", ".dockerignore")):
                continue
            raw = open(path, "rb").read()
            if b"\r\n" in raw:
                open(path, "wb").write(raw.replace(b"\r\n", b"\n"))
                fixed += 1
    gone = 0
    for root, dirs, _ in os.walk(stage.TASK):
        for d in list(dirs):
            if d == "__pycache__":
                shutil.rmtree(os.path.join(root, d), ignore_errors=True)
                dirs.remove(d)
                gone += 1
    print("normalised %d files, removed %d __pycache__ directories" % (fixed, gone))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
