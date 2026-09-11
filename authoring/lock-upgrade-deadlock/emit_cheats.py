"""Write the cheats that are the reference with one reading swapped in.

Each directory under `readings/` holds the file or files of one wrong reading; the cheat
carries all five modules so it installs the same way the reference does, and its second
line says what the reading is. Run after any change to a reading or to the reference.

    python3 authoring/lock-upgrade-deadlock/emit_cheats.py
"""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
TASK = HERE.parents[1] / "tasks" / "lock-upgrade-deadlock"
PARTS = ("mark.py", "item.py", "wait.py", "cyc.py", "txn.py")

HEADERS = {
    "resume-nest": "runs whatever a resumed transaction grants at once, nested, before the "
                   "line goes on",
    "resume-front": "puts transactions granted while another one runs at the front of the "
                    "line instead of the back",
}


def main():
    for d in sorted((HERE / "readings").iterdir()):
        if not d.is_dir():
            continue
        head = HEADERS[d.name]
        lines = ["#!/bin/bash", "# " + head, "set -euo pipefail", ""]
        for part in PARTS:
            src = d / part
            if not src.is_file():
                src = TASK / "solution" / part
            lines += ["cat > /app/hold/%s <<'PYEOF'" % part, src.read_text().rstrip("\n"),
                      "PYEOF", ""]
        out = TASK / "cheat" / ("cheat-%s.sh" % d.name)
        text = "\n".join(lines).rstrip("\n") + "\n"
        assert "\r" not in text
        out.write_text(text, newline="\n")
        out.chmod(0o755)
        print("wrote", out.name)


if __name__ == "__main__":
    main()
