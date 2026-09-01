#!/usr/bin/env python3
"""Stamp a built archive with Unix entry metadata, and say what it changed.

WHY THIS EXISTS. `scripts/package.py` is the kit's script and it is what built every
archive the pipeline has accepted - on Linux. Run on Windows it writes entries with
`create_system = 0` (MS-DOS), and every extractor then ignores the high sixteen bits of
`external_attr` and reads the low byte as DOS attributes. The mode survives a round trip
through Python's own zipfile, so `infolist()` reports `mode 0o755` and any check written
against that passes, and it is discarded the moment the archive is extracted on Linux.
`tests/test.sh` lands non-executable, the verifier never starts, and EVERY submission
scores 0 - the reference and the no-op alike - with `verifier 0s` on both rows.

That has already cost this repo one full pipeline round trip, on
`earliest-change-script`, and the note in CLAUDE.md asking for the check to be added to
`tools/zipcheck.py` is what this pair of tools answers.

WHAT IT WRITES, replicated field for field from the archives the pipeline accepted:

    create_system   3 (Unix); without this nothing else on this list matters
    external_attr   0x01A40180 (0o644) for ordinary files, 0x01ED0180 (0o755) for .sh
    compress_type   8 (deflate)
    date_time       (1980, 1, 1, 0, 0, 0)

    python3 tools/zipfix.py <slug>            rewrite tasks/<slug>.zip in place
    python3 tools/zipfix.py <slug> --check    report only, exit 1 if anything is wrong
"""

from __future__ import annotations

import shutil
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

UNIX = 3
FILE_ATTR = 0x01A40180
EXEC_ATTR = 0x01ED0180
STAMP = (1980, 1, 1, 0, 0, 0)


def wanted(name: str) -> int:
    return EXEC_ATTR if name.endswith(".sh") else FILE_ATTR


def survey(path: Path):
    """Every entry whose metadata would not survive extraction on Linux."""
    bad = []
    with zipfile.ZipFile(path) as z:
        for info in z.infolist():
            if (info.create_system != UNIX
                    or info.external_attr != wanted(info.filename)
                    or info.compress_type != zipfile.ZIP_DEFLATED
                    or info.date_time != STAMP):
                bad.append(info)
    return bad


def rewrite(path: Path) -> int:
    with zipfile.ZipFile(path) as z:
        items = [(i, z.read(i.filename)) for i in z.infolist()]
    spare = path.with_suffix(".zip.tmp")
    with zipfile.ZipFile(spare, "w", zipfile.ZIP_DEFLATED) as out:
        for info, blob in items:
            fresh = zipfile.ZipInfo(info.filename, date_time=STAMP)
            fresh.create_system = UNIX
            fresh.external_attr = wanted(info.filename)
            fresh.compress_type = zipfile.ZIP_DEFLATED
            out.writestr(fresh, blob)
    shutil.move(str(spare), str(path))
    return len(items)


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 2
    path = ROOT / "tasks" / (argv[1] + ".zip")
    if not path.is_file():
        print("no archive at %s" % path)
        return 1

    bad = survey(path)
    print("== %s" % path.name)
    if not bad:
        print("   every entry is Unix, with the mode an extractor will actually honour")
        return 0

    kinds = {}
    for info in bad:
        kinds[info.create_system] = kinds.get(info.create_system, 0) + 1
    print("   %d of the entries would lose their mode on extraction "
          "(create_system counts %s)" % (len(bad), kinds))

    if "--check" in argv:
        print("   run without --check to rewrite them")
        return 1

    n = rewrite(path)
    left = survey(path)
    print("   rewrote %d entries; %d still wrong" % (n, len(left)))
    return 1 if left else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
