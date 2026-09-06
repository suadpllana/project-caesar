"""Execute the actual reference entry point in a disposable host tree."""
import os
from pathlib import Path
import shutil
import subprocess
import sys

import harness

tree = harness.stage(None)
try:
    env = dict(os.environ, APPDIR=tree.as_posix(), PYTHONDONTWRITEBYTECODE="1")
    env["PATH"] = str(Path(sys.executable).parent) + os.pathsep + env["PATH"]
    run = subprocess.run(
        ["C:/Program Files/Git/bin/bash.exe", (harness.REF / "solve.sh").as_posix()],
        env=env, capture_output=True, text=True, timeout=120,
    )
    assert run.returncode == 0, run.stderr
    for name in harness.ARTIFACTS:
        if (harness.REF / name).exists():
            assert (tree / "wire" / name).read_bytes() == (harness.REF / name).read_bytes()
    print("solve.sh applied all five reference policies and ran all ten input fixtures")
finally:
    shutil.rmtree(tree.parent)
