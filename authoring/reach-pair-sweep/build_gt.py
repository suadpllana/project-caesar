"""Freeze the hand-case expectations, and keep the verifier's pristine tree in step.

`gt.json` is the frozen side of the double check: the grader asserts the sealed model still
reproduces it before it grades anything, so a later edit to the model that quietly changes what
correct means fails the run instead of redefining it.

The pristine copy is the environment tree as shipped. The worker drops the submitted collector
into it, so only that one file differs between what the agent ran and what the verifier runs.

    python authoring/reach-pair-sweep/build_gt.py
"""
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
TASK = ROOT / "tasks" / "reach-pair-sweep"
sys.path.insert(0, str(TASK / "tests"))

import cases  # noqa: E402
import model  # noqa: E402


def sync_pristine():
    dst = TASK / "tests" / "pristine"
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(TASK / "environment" / "app_src", dst,
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    return sorted(p.relative_to(dst).as_posix() for p in dst.rglob("*") if p.is_file())


def reference_records():
    """The hand records as the shipped runtime actually prints them, not as the model says."""
    got = {}
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td)
        tree = tmp / "tree"
        shutil.copytree(TASK / "environment" / "app_src", tree)
        shutil.copy(TASK / "solution" / "keep.py", tree / "cyc" / "keep.py")
        for name in cases.ORDER:
            p = tmp / ("%s.txt" % name)
            p.write_text("\n".join(cases.CASES[name]) + "\n", encoding="utf-8")
            r = subprocess.run([sys.executable, "run_prog.py", str(p)], cwd=tree,
                               capture_output=True, text=True, check=True)
            got[name] = r.stdout.splitlines()
    return got


def main():
    files = sync_pristine()
    assert len(files) >= 7, "pristine tree looks short: %s" % files
    print("pristine tree: %d files" % len(files))

    by_model = {n: model.expect(cases.ops(n)) for n in cases.ORDER}
    by_ref = reference_records()
    off = [n for n in cases.ORDER if by_model[n] != by_ref[n]]
    if off:
        print("model and reference disagree on: %s" % off)
        return 1

    out = TASK / "tests" / "gt.json"
    body = json.dumps(by_model, indent=2, sort_keys=True) + "\n"
    out.write_text(body, encoding="utf-8", newline="\n")
    if b"\r" in out.read_bytes():
        raise SystemExit("gt.json picked up CRLF - what ships is the zip, not the commit")
    print("gt.json: %d hand cases, model and reference agreed on all" % len(by_model))
    for n in cases.ORDER:
        print("  %-14s %s" % (n, " | ".join(by_model[n]) or "(nothing released)"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
