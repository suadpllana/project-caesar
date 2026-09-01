#!/usr/bin/env python3
"""Check a built submission zip for the defects that only exist in the archive.

Every other gate in this repo reads the working tree. The pipeline reads the zip, and the
two can disagree - a stale zip, or a file that picked up CRLF on the way in. That gap cost a
bundle-structure rejection on delta-view-retraction (2026-08-13): instruction.md was LF on
disk and CRLF in the archive, so the required final sentence carried a trailing \\r and the
structure check refused it. preflight.py cannot catch that class, because its suffix test
calls .strip() on the last line, which eats the \\r before comparing.

Usage:
    python tools/zipcheck.py <slug>
    python tools/zipcheck.py tasks/<slug>.zip

Exit code 0 if the archive is clean, 1 on any finding.
"""

from __future__ import annotations

import os
import re
import sys
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

SUFFIX_RE = re.compile(
    r"You have (\d+) seconds to complete this task\. Do not cheat by using "
    r"online solutions or hints specific to this task\.$"
)

# Text that ends up executed or parsed on Linux. A stray \r breaks shebang lines with
# "required file not found" and corrupts the graded instruction suffix.
TEXT_SUFFIXES = {".sh", ".py", ".md", ".json", ".toml", ".txt", ".cfg", ".ini"}


def is_text(name: str) -> bool:
    return Path(name).suffix in TEXT_SUFFIXES or Path(name).name == "Dockerfile"


def resolve(arg: str) -> Path:
    p = Path(arg)
    if p.suffix == ".zip" and p.exists():
        return p
    cand = REPO / "tasks" / (arg + ".zip")
    if cand.exists():
        return cand
    print("no such zip: %s" % arg)
    raise SystemExit(1)


def check(zpath: Path) -> int:
    findings: list[str] = []
    zf = zipfile.ZipFile(zpath)
    names = zf.namelist()

    # 1. CRLF anywhere in shipped text. This is the one that bit.
    crlf = [n for n in names if is_text(n) and b"\r\n" in zf.read(n)]
    for n in crlf:
        findings.append("CRLF line endings: %s" % n)

    # 2. Backslash path separators, which unpack to a broken layout on Linux.
    for n in names:
        if "\\" in n:
            findings.append("backslash in archive path: %s" % n)

    # 2b. Unix mode bits that will actually survive extraction.
    #
    #     `scripts/package.py` run on Windows writes entries with create_system = 0
    #     (MS-DOS), and every extractor then ignores the high sixteen bits of
    #     external_attr. The mode survives a round trip through Python's own zipfile, so
    #     reading back `external_attr >> 16` reports 0o755 and passes - which is exactly
    #     the check that passed while an archive was broken. It is discarded the moment
    #     the archive is extracted on Linux: tests/test.sh lands non-executable, the
    #     verifier never starts, and every submission scores 0 including the reference,
    #     with `verifier 0s` on both rows. That cost a full pipeline round trip on
    #     earliest-change-script. tools/zipfix.py rewrites an archive that fails this.
    dos = [i.filename for i in zf.infolist() if i.create_system != 3]
    if dos:
        findings.append(
            "%d entries are stamped MS-DOS (create_system 0) rather than Unix, so their "
            "mode is discarded on extraction - run tools/zipfix.py; first %r"
            % (len(dos), dos[:3]))
    for i in zf.infolist():
        if i.filename.endswith(".sh") and i.create_system == 3 and (i.external_attr >> 16) & 0o111 == 0:
            findings.append("not executable in the archive: %s" % i.filename)

    # 3. The instruction suffix, tested on the raw bytes rather than a stripped line, so a
    #    trailing \r is a finding instead of being silently normalised away.
    instr = [n for n in names if n.endswith("instruction.md")]
    if not instr:
        findings.append("no instruction.md in archive")
    else:
        raw = zf.read(instr[0])
        if b"\r" in raw:
            findings.append("instruction.md contains CR bytes (%d)" % raw.count(b"\r"))
        text = raw.decode("utf-8", "replace")
        if not text.endswith("\n"):
            findings.append("instruction.md does not end with a newline")
        if text.endswith("\n\n"):
            findings.append("instruction.md has more than one trailing newline")
        body = text.rstrip("\n")
        lines = body.split("\n")
        if not lines or not SUFFIX_RE.search(lines[-1]):
            findings.append(
                "instruction.md last line is not the exact required suffix; got %r"
                % (lines[-1][-70:] if lines else "")
            )
        elif len(lines) < 2 or lines[-2] != "":
            findings.append("instruction.md suffix is not preceded by a blank line")

    # 4. Staleness. A zip older than any file it claims to contain is the previous build.
    slug = names[0].split("/")[0] if names else ""
    tree = REPO / "tasks" / slug
    if tree.is_dir():
        ztime = os.path.getmtime(zpath)
        stale = []
        for n in names:
            rel = "/".join(n.split("/")[1:])
            src = tree / rel
            if src.exists() and os.path.getmtime(src) > ztime + 1:
                stale.append(rel)
        for rel in sorted(stale)[:10]:
            findings.append("zip is older than the tree file it ships: %s" % rel)
        if len(stale) > 10:
            findings.append("...and %d more files newer than the zip" % (len(stale) - 10))

    print("== %s" % zpath)
    print("   %d entries" % len(names))
    if findings:
        for f in findings:
            print("   FAIL %s" % f)
        print("\n%d finding(s)" % len(findings))
    else:
        print("   none")
    return len(findings)


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 1
    return 1 if check(resolve(sys.argv[1])) else 0


if __name__ == "__main__":
    raise SystemExit(main())
