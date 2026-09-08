"""Freeze the enumerated expectations, and keep the verifier's pristine copy in step.

Two jobs, both of which have to happen together or the verifier grades a tree that is not
the one the agent starts from:

  gt.json    the expected trace of every enumerated scenario, from the sealed model
  pristine   tests/pristine, a byte copy of environment/app_src with no caches

Every file written here is pinned to LF and checked for a stray carriage return, because a
generator that writes with the platform default is only caught by zipcheck on the archive.
"""
import filecmp
import json
import pathlib
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
TASK = ROOT / "tasks" / "move-clash-merge"
APP = TASK / "environment" / "app_src"
PRISTINE = TASK / "tests" / "pristine"
sys.path.insert(0, str(TASK / "tests"))

import cases  # noqa: E402
import model  # noqa: E402


def sync():
    if PRISTINE.exists():
        shutil.rmtree(PRISTINE)
    shutil.copytree(APP, PRISTINE, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    diff = filecmp.dircmp(APP, PRISTINE)
    assert not diff.left_only and not diff.right_only and not diff.diff_files, "pristine drift"


def freeze():
    out = dict((name, model.replay(cases.CASES[name])) for name in cases.ORDER)
    body = json.dumps(out, indent=1, sort_keys=True) + "\n"
    assert "\r" not in body
    path = TASK / "tests" / "gt.json"
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(body)
    assert "\r" not in path.read_bytes().decode("utf-8")
    return len(out), sum(len(v) for v in out.values())


def main():
    sync()
    n, lines = freeze()
    print("pristine synced from environment/app_src")
    print("gt.json: %d scenarios, %d graded lines" % (n, lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
