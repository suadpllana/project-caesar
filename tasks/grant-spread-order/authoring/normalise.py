"""Force every shipped text file to LF, and clear the authoring scratch out of the way.

Two faults this repo has paid for before, both of which look like content problems and are
neither.

CRLF. `Path.write_text` and Python's text mode open in text mode on Windows, so every "\\n"
becomes a carriage return pair. `delta-view-retraction` was rejected by the bundle
structure check because its instruction ended `...specific to this task.\\r` and no exact
string comparison could match it, on a file nobody had edited. `scripts/preflight.py`
cannot catch it - its suffix test strips the line before the regex runs - so the check lives
in `tools/zipcheck.py` and the fix lives here. Worse than the instruction: CRLF inside
`tests/pristine` is copied into the verifier image and executed.

SCRATCH. `scripts/package.py` ships the whole `authoring/` directory, so a temporary JSON
report or a staging tree left behind under it goes into the submission. Everything this
task writes for its own use is named with a leading underscore, and that is what gets
cleared.

    python authoring/normalise.py
"""

import pathlib
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

TEXT = {".py", ".md", ".sh", ".toml", ".txt", ".json", ".cfg", ".ini", ""}
SKIP = {"__pycache__", ".git"}


def shipped():
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file():
            continue
        if any(part in SKIP for part in path.parts):
            continue
        if path.suffix.lower() in TEXT or path.name == "Dockerfile":
            yield path


def main():
    gone = []
    for path in sorted((ROOT / "authoring").glob("_*")):
        if path.is_dir():
            shutil.rmtree(path, ignore_errors=True)
        else:
            path.unlink()
        gone.append(path.name)

    fixed = []
    for path in shipped():
        raw = path.read_bytes()
        if b"\r\n" not in raw and b"\r" not in raw:
            continue
        path.write_bytes(raw.replace(b"\r\n", b"\n").replace(b"\r", b"\n"))
        fixed.append(path.relative_to(ROOT).as_posix())

    print("cleared %d scratch entries: %s" % (len(gone), ", ".join(gone) or "none"))
    print("normalised %d files to LF" % len(fixed))
    for name in fixed:
        print("  ", name)
    return 0


if __name__ == "__main__":
    sys.exit(main())
