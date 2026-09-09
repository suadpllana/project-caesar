"""Freeze the hand-case expectations, and keep the verifier's pristine tree in step.

`gt.json` is the frozen side of the double check: the grader asserts the sealed model still
reproduces it before it grades anything, so a later edit to the model that quietly changes
what correct means fails the run instead of redefining it. The reference is driven through
the shipped runtime over the same cases first, and this refuses to write anything the two
disagree on.

Written with LF pinned: an earlier archive shipped this file CRLF because it was written
with the platform default on Windows, and only zipcheck on the built archive noticed.

    python authoring/repair-orderbook-engine/build_gt.py
"""
import json
import pathlib
import shutil
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
TASK = ROOT / "tasks" / "repair-orderbook-engine"
sys.path.insert(0, str(TASK / "tests"))
sys.path.insert(0, str(ROOT / "authoring" / "repair-orderbook-engine"))

import agree  # noqa: E402
import cases  # noqa: E402
import oracle  # noqa: E402


def sync_pristine():
    dst = TASK / "tests" / "pristine"
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(TASK / "environment" / "app_src", dst,
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    return sorted(p.relative_to(dst).as_posix() for p in dst.rglob("*") if p.is_file())


def main():
    files = sync_pristine()
    assert len(files) >= 15, "pristine tree looks short: %s" % files
    print("pristine tree: %d files" % len(files))

    tmp, app = agree.tree_with(TASK / "solution")
    try:
        run = agree.runtime(app)
        by_ref = {n: run(cases.SESS[n]) for n in sorted(cases.SESS)}
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    by_model = {n: [list(r) for r in oracle.solve(cases.SESS[n])] for n in sorted(cases.SESS)}
    bad = [n for n in by_model if by_model[n] != by_ref[n]]
    if bad:
        for n in bad[:6]:
            print("DISAGREE %s: %s" % (n, agree.first_diff(by_ref[n], by_model[n])))
        raise SystemExit("reference and model disagree on %d hand cases" % len(bad))

    out = TASK / "tests" / "gt.json"
    text = json.dumps({"cases": by_model}, indent=1, sort_keys=True) + "\n"
    assert "\r" not in text
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    raw = out.read_bytes()
    assert b"\r" not in raw
    print("gt.json: %d cases, %d bytes, LF only" % (len(by_model), len(raw)))


if __name__ == "__main__":
    main()
