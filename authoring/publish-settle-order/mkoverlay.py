"""Build a full six-file overlay from the reference plus one reading's replacements."""
import pathlib
import shutil
import sys
import tempfile

import lab

PARTS = lab.PARTS


def build(reading: pathlib.Path) -> pathlib.Path:
    out = pathlib.Path(tempfile.mkdtemp(prefix="pso-ov-"))
    for name in PARTS:
        shutil.copy(lab.TASK / "solution" / name, out / name)
    fired = 0
    for one in sorted(reading.glob("*.py")):
        if one.name not in PARTS:
            raise SystemExit("reading %s replaces unknown file %s" % (reading.name, one.name))
        if one.read_text() == (lab.TASK / "solution" / one.name).read_text():
            raise SystemExit("reading %s: %s is identical to the reference" % (reading.name, one.name))
        shutil.copy(one, out / one.name)
        fired += 1
    if not fired:
        raise SystemExit("reading %s replaces nothing" % reading.name)
    return out


if __name__ == "__main__":
    print(build(pathlib.Path(sys.argv[1])))
