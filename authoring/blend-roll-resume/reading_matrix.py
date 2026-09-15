"""For each wrong reading, every enumerated case that fails it.

readingcheck reports the first case that separates a reading, which is enough to know the set
pins the rule but not enough to write down which case names it. The prose in task.toml claims
specific cases, and a claim about a check is not evidence until the check has been run.
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import readings  # noqa: E402


def main():
    ref = readings.REFERENCE
    want = {name: readings.run(ref, text) for name, text in readings.enumerated()}
    rows = {}
    for name, files in sorted(readings.READINGS.items()):
        import shutil
        import tempfile
        room = Path(tempfile.mkdtemp(prefix="matrix-"))
        for p in Path(ref).glob("*.py"):
            shutil.copyfile(p, room / p.name)
        for fn, src in files.items():
            (room / fn).write_text(src, encoding="utf-8")
        hits = []
        for case, text in readings.enumerated():
            try:
                got = readings.run(room, text)
            except Exception as exc:
                hits.append("%s(%s)" % (case, type(exc).__name__))
                continue
            if got != want[case]:
                hits.append(case)
        shutil.rmtree(room, ignore_errors=True)
        rows[name] = hits
        print("%-18s %2d  %s" % (name, len(hits), " ".join(hits) if hits else "NONE"))
    empty = [n for n, h in rows.items() if not h]
    print("\nreadings with no enumerated case: %s" % (", ".join(empty) or "none"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
