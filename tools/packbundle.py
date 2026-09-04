"""Package a task bundle without the authoring directory.

The quality review blocked `alias-settle-report` on 2026-09-04 for extraneous
files: `authoring/` is development tooling that nothing in the build, run, solve
or verify path requires, and several of its scripts import repo tools that do not
ship, so they cannot even run from inside the bundle.

`scripts/package.py` and `scripts/preflight.py` are the kit's and are not to be
edited, and their shared exclusion list has no entry for `authoring`. So this
stages the bundle without it and hands the staged copy to the kit's packager,
which keeps the archive the kit's work and the exclusion this repo's.

Anything the authoring directory proves - that ground truth was independently
rebuilt, that five alternative correct implementations score 1 - is a claim that
belongs in task.toml, where the reviewer reads it, not a directory of scripts.
"""

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DROP = ("authoring",)


def main(argv):
    if len(argv) < 2:
        print("usage: packbundle.py <slug> [--force]")
        return 2
    slug = argv[1]
    root = REPO / "tasks" / slug
    if not root.is_dir():
        print("no such task: %s" % root)
        return 1
    out = REPO / "tasks" / ("%s.zip" % slug)
    box = Path(tempfile.mkdtemp(prefix="pack-"))
    try:
        staged = box / slug
        shutil.copytree(root, staged,
                        ignore=shutil.ignore_patterns(*DROP, "__pycache__", "*.pyc"))
        left = sorted(p.name for p in staged.iterdir())
        print("staged without %s: %s" % (", ".join(DROP), " ".join(left)))
        cmd = [sys.executable, str(REPO / "scripts" / "package.py"),
               str(staged), "-o", str(out)] + list(argv[2:])
        return subprocess.call(cmd)
    finally:
        shutil.rmtree(box, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
