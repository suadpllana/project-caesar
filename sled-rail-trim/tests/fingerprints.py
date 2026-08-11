"""Fingerprint the files the agent was told not to touch.

Fails closed: a missing reference copy is itself a violation, and so is a file
gone from the working tree. If this reports anything, nothing is graded.
"""

import hashlib
import pathlib

PROTECTED = (
    "include/sled.h",
    "src/sandbox.c",
    "Makefile",
)


def _digest(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check(app_dir: str, pristine_dir: str) -> list[str]:
    app = pathlib.Path(app_dir)
    pristine = pathlib.Path(pristine_dir)
    problems: list[str] = []

    for rel in PROTECTED:
        want = pristine / rel
        got = app / rel
        if not want.exists():
            problems.append(f"reference copy missing for {rel} -- refusing to grade")
            continue
        if not got.exists():
            problems.append(f"{rel} is gone from the working tree")
            continue
        if _digest(want) != _digest(got):
            problems.append(f"{rel} has been modified")

    return problems
