"""Refresh tests/pristine from environment/app_src.

The verifier compares the tree that ran against this copy, so it has to be the same bytes.
"""
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main():
    src = ROOT / "environment" / "app_src"
    dst = ROOT / "tests" / "pristine"
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    n = sum(1 for p in dst.rglob("*") if p.is_file())
    print("pristine refreshed, %d files" % n)


if __name__ == "__main__":
    main()
